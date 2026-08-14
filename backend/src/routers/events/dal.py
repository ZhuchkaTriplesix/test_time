import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.events.models import Event, EventType
from src.routers.tickets.models import SLAStatus, Ticket, TicketStatus


class EventsDAL:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_event_on_conflict_do_nothing(
        self,
        external_event_id: str,
        event_type: EventType,
        received_at: datetime,
        ticket_id: uuid.UUID | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Event | None:
        """Insert event with ON CONFLICT (external_event_id) DO NOTHING.

        Returns Event instance if inserted, or None if duplicate.
        """
        stmt = (
            insert(Event)
            .values(
                id=uuid.uuid4(),
                external_event_id=external_event_id,
                event_type=event_type,
                ticket_id=ticket_id,
                received_at=received_at,
                payload=payload,
            )
            .on_conflict_do_nothing(index_elements=["external_event_id"])
            .returning(Event)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_event_by_external_id(self, external_event_id: str) -> Event | None:
        stmt = select(Event).where(Event.external_event_id == external_event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_ticket(
        self,
        external_client_id: str,
        topic: str,
        content: str,
        created_at: datetime,
    ) -> Ticket:
        ticket = Ticket(
            id=uuid.uuid4(),
            external_client_id=external_client_id,
            topic=topic,
            content=content,
            status=TicketStatus.OPEN,
            sla_status=SLAStatus.NORMAL,
            created_at=created_at,
        )
        self.session.add(ticket)
        await self.session.flush()
        return ticket

    async def close_ticket(
        self,
        ticket_id: uuid.UUID | None = None,
        external_client_id: str | None = None,
        closed_at: datetime | None = None,
    ) -> Ticket | None:
        """Find an open ticket by ticket_id or external_client_id and close it."""
        if closed_at is None:
            closed_at = datetime.now(UTC)

        stmt = select(Ticket).where(Ticket.status == TicketStatus.OPEN)
        if ticket_id is not None:
            stmt = stmt.where(Ticket.id == ticket_id)
        elif external_client_id is not None:
            stmt = stmt.where(Ticket.external_client_id == external_client_id).order_by(
                Ticket.created_at.desc()
            )
        else:
            return None

        result = await self.session.execute(stmt)
        ticket = result.scalars().first()
        if ticket is None:
            return None

        # Calculate first response time
        ticket.status = TicketStatus.CLOSED
        ticket.closed_at = closed_at
        ticket.first_response_time = closed_at - ticket.created_at
        await self.session.flush()
        return ticket
