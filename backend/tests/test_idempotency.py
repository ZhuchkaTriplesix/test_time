import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.events.models import Event
from src.routers.tickets.models import Ticket


@pytest.mark.asyncio
async def test_idempotency_concurrent_20_events(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Scenario 1: Concurrency idempotency test.

    Sends 20 duplicate client events concurrently using asyncio.gather.
    Asserts:
    - Only 1 ticket is created in the database.
    - Only 1 raw event record is stored in the events table.
    - /api/tickets returns exactly 1 open ticket.
    - HTTP responses are 201 Created for the winner and 200 OK for the duplicates.
    """
    external_event_id = "test_event_concurrent_unique_101"
    payload = {
        "external_event_id": external_event_id,
        "event_type": "client",
        "external_client_id": "client_tg_999",
        "topic": "Платежи",
        "content": "Не проходит оплата картой",
    }

    # Send 20 parallel requests with identical payload
    tasks = [async_client.post("/api/events", json=payload) for _ in range(20)]
    responses = await asyncio.gather(*tasks)

    # Status codes verification
    status_codes = [r.status_code for r in responses]
    created_count = status_codes.count(201)
    duplicate_count = status_codes.count(200)

    # Exactly 1 winner should get 201 Created, remaining 19 get 200 OK
    assert created_count == 1, f"Expected 1 Created (201), got {created_count}"
    assert duplicate_count == 19, f"Expected 19 Duplicates (200), got {duplicate_count}"

    # Verify database state
    ticket_count = (await db_session.execute(select(func.count(Ticket.id)))).scalar()
    event_count = (await db_session.execute(select(func.count(Event.id)))).scalar()

    assert ticket_count == 1, f"Expected exactly 1 ticket in database, found {ticket_count}"
    assert event_count == 1, f"Expected exactly 1 event in database, found {event_count}"

    # Verify GET /api/tickets returns 1 ticket
    tickets_res = await async_client.get("/api/tickets")
    assert tickets_res.status_code == 200
    tickets_data = tickets_res.json()
    assert tickets_data["total"] == 1
    assert tickets_data["tickets"][0]["external_client_id"] == "client_tg_999"
