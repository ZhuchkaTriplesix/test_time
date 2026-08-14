import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.outbox.models import OutboxEvent
from src.routers.tickets.models import SLAStatus, Ticket, TicketStatus


async def simulate_sla_sweep(
    session: AsyncSession,
    warning_seconds: int = 60,
    overdue_seconds: int = 180,
) -> int:
    """Helper implementing the exact SLA Sweeper logic for tests."""
    now = datetime.now(UTC)
    warning_cutoff = now - timedelta(seconds=warning_seconds)
    overdue_cutoff = now - timedelta(seconds=overdue_seconds)

    transitions = 0

    # 1. Overdue transitions
    stmt_overdue = (
        select(Ticket)
        .where(Ticket.status == TicketStatus.OPEN)
        .where(Ticket.sla_status.in_([SLAStatus.NORMAL, SLAStatus.WARNING]))
        .where(Ticket.created_at <= overdue_cutoff)
    )
    overdue_tickets = (await session.execute(stmt_overdue)).scalars().all()
    for t in overdue_tickets:
        t.sla_status = SLAStatus.OVERDUE
        session.add(
            OutboxEvent(
                id=uuid.uuid4(),
                ticket_id=t.id,
                event_type="sla_overdue",
                payload={"ticket_id": str(t.id), "sla_status": "overdue"},
                available_at=now,
                created_at=now,
            )
        )
        transitions += 1

    # 2. Warning transitions
    stmt_warning = (
        select(Ticket)
        .where(Ticket.status == TicketStatus.OPEN)
        .where(Ticket.sla_status == SLAStatus.NORMAL)
        .where(Ticket.created_at <= warning_cutoff)
        .where(Ticket.created_at > overdue_cutoff)
    )
    warning_tickets = (await session.execute(stmt_warning)).scalars().all()
    for t in warning_tickets:
        t.sla_status = SLAStatus.WARNING
        session.add(
            OutboxEvent(
                id=uuid.uuid4(),
                ticket_id=t.id,
                event_type="sla_warning",
                payload={"ticket_id": str(t.id), "sla_status": "warning"},
                available_at=now,
                created_at=now,
            )
        )
        transitions += 1

    await session.commit()
    return transitions


@pytest.mark.asyncio
async def test_sla_deduplication_and_state_transitions(db_session: AsyncSession):
    """Scenario 3: Protection against duplicate alerts and proper warning -> overdue transition.

    1. Creates a ticket aged 70s (should trigger WARNING).
    2. Runs sweep cycle -> transitions to WARNING, creates 1 outbox event.
    3. Runs sweep cycle again -> NO new outbox events created.
    4. Ages the ticket to 200s (should trigger OVERDUE).
    5. Runs sweep cycle -> transitions to OVERDUE, creates exactly 1 new outbox event (total 2).
    6. Runs sweep cycle again -> NO new outbox events created (total remains 2).
    """
    now = datetime.now(UTC)

    # 1. Create a ticket aged 70 seconds (breached warning threshold of 60s)
    ticket = Ticket(
        id=uuid.uuid4(),
        external_client_id="client_sla_test",
        topic="SLA Test",
        content="Testing SLA alerts",
        status=TicketStatus.OPEN,
        sla_status=SLAStatus.NORMAL,
        created_at=now - timedelta(seconds=70),
    )
    db_session.add(ticket)
    await db_session.commit()

    # 2. First sweep run -> normal -> warning
    t1 = await simulate_sla_sweep(db_session)
    assert t1 == 1

    outbox_count = (await db_session.execute(select(func.count(OutboxEvent.id)))).scalar()
    assert outbox_count == 1, "Expected 1 warning alert created in outbox"

    # Verify ticket status updated
    await db_session.refresh(ticket)
    assert ticket.sla_status == SLAStatus.WARNING

    # 3. Repeated sweep run -> must NOT create duplicate warning
    t2 = await simulate_sla_sweep(db_session)
    assert t2 == 0

    outbox_count = (await db_session.execute(select(func.count(OutboxEvent.id)))).scalar()
    assert outbox_count == 1, "Expected outbox count to remain 1 after repeated sweep"

    # 4. Age the ticket past overdue threshold (200 seconds ago)
    ticket.created_at = now - timedelta(seconds=200)
    await db_session.commit()

    # 5. Sweep run -> warning -> overdue
    t3 = await simulate_sla_sweep(db_session)
    assert t3 == 1

    outbox_count = (await db_session.execute(select(func.count(OutboxEvent.id)))).scalar()
    assert outbox_count == 2, "Expected exactly 1 new overdue alert (total 2)"

    await db_session.refresh(ticket)
    assert ticket.sla_status == SLAStatus.OVERDUE

    # 6. Repeated sweep run on overdue ticket -> must NOT create duplicate overdue
    t4 = await simulate_sla_sweep(db_session)
    assert t4 == 0

    outbox_count = (await db_session.execute(select(func.count(OutboxEvent.id)))).scalar()
    assert outbox_count == 2, (
        "Expected outbox count to remain 2 after repeated sweep on overdue ticket"
    )
