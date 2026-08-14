"""Тест обязательного сценария №4: Атомарность транзакций и откат при сбоях.

Назначение:
- Симуляция сбоя БД при создании тикета после вставки события.
- Проверка полного отката транзакции (отсутствие битых/одиночных записей).
- Проверка успешной повторной доставки того же события без задвоения сущностей.
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.events.dal import EventsDAL
from src.routers.events.models import Event
from src.routers.tickets.models import Ticket


@pytest.mark.asyncio
async def test_atomicity_and_rollback_on_failure(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Scenario 4: Transactional atomicity test.

    1. Simulates a sudden failure in `EventsDAL.create_ticket` right after event insertion.
    2. Verifies that the entire transaction is rolled back (no orphan event, no ticket).
    3. Retries the same event without simulated failure.
    4. Verifies that the event and ticket are both created successfully in consistent state.
    """
    event_payload = {
        "external_event_id": "evt_atomicity_test_404",
        "event_type": "client",
        "external_client_id": "client_atomic_user",
        "topic": "Техподдержка",
        "content": "Сбой транзакции",
    }

    # 1. Inject artificial failure into EventsDAL.create_ticket
    with patch.object(
        EventsDAL, "create_ticket", side_effect=RuntimeError("Simulated Database Crash")
    ):
        try:
            response = await async_client.post("/api/events", json=event_payload)
            assert response.status_code == 500
        except RuntimeError:
            pass

    # 2. Verify complete transaction rollback: neither Event nor Ticket should exist
    event_count = (
        await db_session.execute(
            select(func.count(Event.id)).where(Event.external_event_id == "evt_atomicity_test_404")
        )
    ).scalar()
    ticket_count = (
        await db_session.execute(
            select(func.count(Ticket.id)).where(Ticket.external_client_id == "client_atomic_user")
        )
    ).scalar()

    assert event_count == 0, f"Expected 0 events due to rollback, found {event_count}"
    assert ticket_count == 0, f"Expected 0 tickets due to rollback, found {ticket_count}"

    # 3. Retry sending the same event normally (without failure)
    retry_response = await async_client.post("/api/events", json=event_payload)
    assert retry_response.status_code == 201
    retry_data = retry_response.json()
    assert retry_data["status"] == "created"

    # 4. Verify that now exactly 1 Event and 1 Ticket exist
    event_count_after = (
        await db_session.execute(
            select(func.count(Event.id)).where(Event.external_event_id == "evt_atomicity_test_404")
        )
    ).scalar()
    ticket_count_after = (
        await db_session.execute(
            select(func.count(Ticket.id)).where(Ticket.external_client_id == "client_atomic_user")
        )
    ).scalar()

    assert event_count_after == 1, "Expected 1 event after retry"
    assert ticket_count_after == 1, "Expected 1 ticket after retry"
