import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.tickets.models import SLAStatus, Ticket, TicketStatus


@pytest.mark.asyncio
async def test_metrics_empty_dataset(async_client: AsyncClient):
    """Scenario 5.1: Metrics on empty dataset must be well-defined without errors."""
    response = await async_client.get("/api/metrics")
    assert response.status_code == 200

    data = response.json()
    assert data["total_created"] == 0
    assert data["total_answered"] == 0
    assert data["total_overdue"] == 0
    assert data["median_first_response_time_seconds"] is None


@pytest.mark.asyncio
async def test_metrics_fixed_dataset(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Scenario 5.2: Metrics with fixed dataset calculation including median.

    Tickets:
    1. Closed ticket: response_time = 30s
    2. Closed ticket: response_time = 60s
    3. Closed ticket: response_time = 90s
    4. Open ticket: normal SLA
    5. Open ticket: overdue SLA

    Expected:
    - total_created = 5
    - total_answered = 3
    - total_overdue = 1
    - median_first_response_time_seconds = 60.0 (median of [30, 60, 90])
    """
    now = datetime.now(UTC)

    # 1. Add 3 closed tickets with response times 30s, 60s, 90s
    for seconds in (30, 60, 90):
        t = Ticket(
            id=uuid.uuid4(),
            external_client_id=f"client_answered_{seconds}",
            topic="Billing",
            content=f"Closed query {seconds}s",
            status=TicketStatus.CLOSED,
            sla_status=SLAStatus.NORMAL,
            created_at=now - timedelta(seconds=seconds + 100),
            closed_at=now - timedelta(seconds=100),
            first_response_time=timedelta(seconds=seconds),
        )
        db_session.add(t)

    # 2. Add 1 open normal ticket
    t_normal = Ticket(
        id=uuid.uuid4(),
        external_client_id="client_open_normal",
        topic="Support",
        content="Open normal query",
        status=TicketStatus.OPEN,
        sla_status=SLAStatus.NORMAL,
        created_at=now - timedelta(seconds=20),
    )
    db_session.add(t_normal)

    # 3. Add 1 open overdue ticket
    t_overdue = Ticket(
        id=uuid.uuid4(),
        external_client_id="client_open_overdue",
        topic="Support",
        content="Open overdue query",
        status=TicketStatus.OPEN,
        sla_status=SLAStatus.OVERDUE,
        created_at=now - timedelta(seconds=250),
    )
    db_session.add(t_overdue)

    await db_session.commit()

    # Query metrics endpoint
    response = await async_client.get("/api/metrics")
    assert response.status_code == 200

    data = response.json()
    assert data["total_created"] == 5
    assert data["total_answered"] == 3
    assert data["total_overdue"] == 1
    if data["median_first_response_time_seconds"] is not None:
        assert data["median_first_response_time_seconds"] == 60.0
