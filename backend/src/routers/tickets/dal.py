from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.tickets.models import Ticket, TicketStatus


class TicketsDAL:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_open_tickets(self, topic: str | None = None) -> list[Ticket]:
        """Fetch open tickets, optionally filtered by topic."""
        stmt = (
            select(Ticket)
            .where(Ticket.status == TicketStatus.OPEN)
            .order_by(Ticket.created_at.asc())
        )
        if topic:
            stmt = stmt.where(Ticket.topic == topic)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_distinct_topics(self) -> list[str]:
        """Fetch all unique topics present in the database."""
        stmt = select(distinct(Ticket.topic)).order_by(Ticket.topic.asc())
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all() if row[0]]
