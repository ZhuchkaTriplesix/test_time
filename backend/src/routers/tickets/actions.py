from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.routers.tickets.dal import TicketsDAL
from src.routers.tickets.models import SLAStatus
from src.routers.tickets.schemas import TicketListResponse, TicketResponse


def compute_dynamic_sla_status(
    wait_time_seconds: float,
    warning_threshold: int,
    overdue_threshold: int,
) -> SLAStatus:
    """Determine real-time SLA status based on elapsed wait seconds."""
    if wait_time_seconds >= overdue_threshold:
        return SLAStatus.OVERDUE
    if wait_time_seconds >= warning_threshold:
        return SLAStatus.WARNING
    return SLAStatus.NORMAL


async def list_open_tickets(
    session: AsyncSession,
    topic: str | None = None,
) -> TicketListResponse:
    """Fetch open tickets with dynamic wait times and real-time SLA statuses."""
    settings = get_settings()
    dal = TicketsDAL(session)
    now = datetime.now(UTC)

    tickets = await dal.get_open_tickets(topic=topic)
    distinct_topics = await dal.get_distinct_topics()

    ticket_responses: list[TicketResponse] = []
    for t in tickets:
        # Calculate dynamic elapsed wait time
        wait_seconds = max(0.0, (now - t.created_at).total_seconds())

        # Real-time dynamic SLA status computation
        current_sla = compute_dynamic_sla_status(
            wait_time_seconds=wait_seconds,
            warning_threshold=settings.SLA_WARNING_SECONDS,
            overdue_threshold=settings.SLA_OVERDUE_SECONDS,
        )

        first_resp_seconds = (
            t.first_response_time.total_seconds() if t.first_response_time else None
        )

        ticket_responses.append(
            TicketResponse(
                id=t.id,
                external_client_id=t.external_client_id,
                topic=t.topic,
                content=t.content,
                status=t.status,
                sla_status=current_sla,
                created_at=t.created_at,
                closed_at=t.closed_at,
                wait_time_seconds=round(wait_seconds, 1),
                first_response_time_seconds=first_resp_seconds,
            )
        )

    return TicketListResponse(
        tickets=ticket_responses,
        total=len(ticket_responses),
        available_topics=distinct_topics,
    )
