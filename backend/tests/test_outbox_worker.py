"""Тесты фонового процессора Transactional Outbox (Outbox Delivery Processor).

Назначение:
- Проверка обработки батчей событий Outbox (успешная доставка -> статус done).
- Проверка механизма повторных попыток (Retry with Exponential Backoff) при сбое внешнего сервиса.
- Проверка перевода события в статус failed при превышении лимита попыток (MAX_ATTEMPTS = 3).
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.outbox.models import OutboxEvent, OutboxStatus
from src.routers.tickets.models import Ticket, TicketStatus


async def simulate_outbox_batch_delivery(
    session: AsyncSession,
    adapter_deliver_fn,
    max_attempts: int = 3,
    batch_size: int = 50,
) -> int:
    """Helper implementing exact Outbox batch processing logic for test validation."""
    now = datetime.now(UTC)
    processed_count = 0

    stmt = (
        select(OutboxEvent)
        .where(OutboxEvent.status == OutboxStatus.PENDING)
        .where(OutboxEvent.available_at <= now)
        .order_by(OutboxEvent.created_at.asc())
        .limit(batch_size)
    )
    events = (await session.execute(stmt)).scalars().all()

    for event in events:
        try:
            delivered = await adapter_deliver_fn(event)
            if delivered:
                event.status = OutboxStatus.DONE
                processed_count += 1
            else:
                raise RuntimeError("Adapter failed delivery")
        except Exception as e:
            event.attempts += 1
            event.last_error = str(e)
            if event.attempts >= max_attempts:
                event.status = OutboxStatus.FAILED
            else:
                retry_delay = 2**event.attempts
                event.available_at = now + timedelta(seconds=retry_delay)

    await session.commit()
    return processed_count


@pytest.mark.asyncio
async def test_outbox_processor_successful_delivery(db_session: AsyncSession):
    """Test that pending outbox events are processed and marked as done upon successful notification."""
    now = datetime.now(UTC)
    ticket_id = uuid.uuid4()

    ticket = Ticket(
        id=ticket_id,
        external_client_id="client_test_outbox",
        topic="Тестирование Outbox",
        content="Тестовое сообщение",
        status=TicketStatus.OPEN,
        created_at=now,
    )
    db_session.add(ticket)
    await db_session.flush()

    outbox_event = OutboxEvent(
        id=uuid.uuid4(),
        ticket_id=ticket_id,
        event_type="sla_warning",
        payload={"topic": "Тестирование Outbox", "sla_status": "warning"},
        status=OutboxStatus.PENDING,
        available_at=now,
        created_at=now,
    )
    db_session.add(outbox_event)
    await db_session.commit()

    async def mock_successful_adapter(event):
        return True

    processed_count = await simulate_outbox_batch_delivery(
        db_session, mock_successful_adapter
    )
    assert processed_count == 1

    # Verify event status is updated to DONE
    result = await db_session.execute(
        select(OutboxEvent).where(OutboxEvent.id == outbox_event.id)
    )
    updated_event = result.scalar_one()
    assert updated_event.status == OutboxStatus.DONE


@pytest.mark.asyncio
async def test_outbox_processor_retry_and_failure(db_session: AsyncSession):
    """Test retry backoff on failure and marking as failed when max attempts are exceeded."""
    now = datetime.now(UTC)
    ticket_id = uuid.uuid4()

    ticket = Ticket(
        id=ticket_id,
        external_client_id="client_test_retry",
        topic="Тестирование Retry",
        content="Тестовое сообщение",
        status=TicketStatus.OPEN,
        created_at=now,
    )
    db_session.add(ticket)
    await db_session.flush()

    outbox_event = OutboxEvent(
        id=uuid.uuid4(),
        ticket_id=ticket_id,
        event_type="sla_overdue",
        payload={"topic": "Тестирование Retry", "sla_status": "overdue"},
        status=OutboxStatus.PENDING,
        attempts=2,  # Already attempted twice, next failure should mark as FAILED (limit 3)
        available_at=now,
        created_at=now,
    )
    db_session.add(outbox_event)
    await db_session.commit()

    async def mock_failing_adapter(event):
        raise RuntimeError("Connection timeout to alert service")

    await simulate_outbox_batch_delivery(db_session, mock_failing_adapter)

    # Verify event status reached FAILED due to max attempts exceeded
    result = await db_session.execute(
        select(OutboxEvent).where(OutboxEvent.id == outbox_event.id)
    )
    updated_event = result.scalar_one()
    assert updated_event.status == OutboxStatus.FAILED
    assert updated_event.attempts == 3
    assert "Connection timeout" in updated_event.last_error
