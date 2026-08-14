import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.events.dal import EventsDAL
from src.routers.events.models import EventType
from src.routers.events.schemas import EventIngestRequest, EventIngestResponse

logger = logging.getLogger(__name__)


async def ingest_event(
    request: EventIngestRequest,
    session: AsyncSession,
) -> tuple[EventIngestResponse, bool]:
    """Ingest external event atomically and idempotently.

    Returns:
        tuple[EventIngestResponse, bool]: (response_model, is_newly_created)
    """
    dal = EventsDAL(session)
    event_timestamp = request.received_at or datetime.now(UTC)

    # 1. Attempt to insert raw event (idempotency barrier)
    event = await dal.insert_event_on_conflict_do_nothing(
        external_event_id=request.external_event_id,
        event_type=request.event_type,
        received_at=event_timestamp,
        ticket_id=request.ticket_id,
        payload=request.payload,
    )

    if event is None:
        # Duplicate event detected!
        existing_event = await dal.get_event_by_external_id(request.external_event_id)
        existing_ticket_id = existing_event.ticket_id if existing_event else None
        logger.info(
            "Duplicate event ignored: %s (type=%s)",
            request.external_event_id,
            request.event_type,
        )
        return (
            EventIngestResponse(
                status="duplicate",
                external_event_id=request.external_event_id,
                ticket_id=existing_ticket_id,
                event_type=request.event_type,
                message="Event already processed (idempotent ignore)",
            ),
            False,
        )

    # 2. Process business logic based on event type
    associated_ticket_id: uuid.UUID | None = None

    if request.event_type == EventType.CLIENT:
        # Client message -> Create new ticket
        client_id = request.external_client_id or f"client_{request.external_event_id}"
        topic = request.topic or "General"
        content = request.content or "No content provided"

        ticket = await dal.create_ticket(
            external_client_id=client_id,
            topic=topic,
            content=content,
            created_at=event_timestamp,
        )
        event.ticket_id = ticket.id
        associated_ticket_id = ticket.id
        logger.info(
            "Created new ticket %s from event %s (client=%s, topic=%s)",
            ticket.id,
            request.external_event_id,
            client_id,
            topic,
        )

    elif request.event_type == EventType.AGENT:
        # Agent response -> Close ticket and record first_response_time
        ticket = await dal.close_ticket(
            ticket_id=request.ticket_id,
            external_client_id=request.external_client_id,
            closed_at=event_timestamp,
        )
        if ticket is not None:
            associated_ticket_id = ticket.id
            event.ticket_id = ticket.id
            logger.info(
                "Closed ticket %s from agent response %s (response_time=%s)",
                ticket.id,
                request.external_event_id,
                ticket.first_response_time,
            )
        else:
            logger.warning(
                "Agent event %s received but no matching open ticket found",
                request.external_event_id,
            )

    return (
        EventIngestResponse(
            status="created",
            external_event_id=request.external_event_id,
            ticket_id=associated_ticket_id,
            event_type=request.event_type,
            message="Event processed successfully",
        ),
        True,
    )
