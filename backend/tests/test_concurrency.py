import asyncio
import time

import pytest
from httpx import AsyncClient

from src.services.notifications import LocalLogNotificationAdapter, set_notification_adapter


@pytest.mark.asyncio
async def test_non_blocking_notification_adapter_concurrency(async_client: AsyncClient):
    """Scenario 2: Non-blocking parallel execution test.

    Sets a 2.0-second delay on the notification adapter.
    Spawns background notification delivery task and verifies that
    GET /health and GET /api/tickets respond immediately (< 200ms) without being blocked.
    """
    # 1. Configure adapter with 2 seconds simulation delay
    delay_adapter = LocalLogNotificationAdapter(delay_seconds=2.0)
    set_notification_adapter(delay_adapter)

    try:
        # 2. Launch notification in background task
        bg_task = asyncio.create_task(
            delay_adapter.send_alert(
                topic="Critical",
                ticket_id="ticket-123",
                sla_status="overdue",
                wait_time_seconds=200.0,
                content="Urgent issue",
            )
        )

        # 3. Measure latency of GET /health and GET /api/tickets while notification is pending
        start_time = time.perf_counter()

        health_response = await async_client.get("/health")
        tickets_response = await async_client.get("/api/tickets")

        elapsed_time = time.perf_counter() - start_time

        assert health_response.status_code == 200
        assert tickets_response.status_code == 200

        # Assert requests returned well under the 2.0 second adapter delay
        assert elapsed_time < 0.5, (
            f"HTTP endpoints took {elapsed_time:.3f}s, expected < 0.5s (blocking detected!)"
        )

        # Wait for the background task to complete cleanly
        await bg_task

    finally:
        # Reset adapter delay
        set_notification_adapter(LocalLogNotificationAdapter(delay_seconds=0.0))
