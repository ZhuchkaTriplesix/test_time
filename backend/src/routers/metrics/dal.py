"""Слой доступа к данным (DAL) для расчета агрегированных аналитических метрик.

Назначение:
- Расчет количества созданных, закрытых и просроченных тикетов в СУБД.
- Вычисление непрерывной медианы времени ответа непосредственно на уровне PostgreSQL
  через `func.percentile_cont(0.5).within_group(...)` без загрузки строк в память Python.
"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.tickets.models import SLAStatus, Ticket, TicketStatus


class MetricsDAL:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_metrics(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict:
        """Calculate aggregated metrics directly in PostgreSQL.

        Uses percentile_cont(0.5) to compute the continuous median on the database level.
        """
        # Base filter condition
        created_filter = []
        if date_from:
            created_filter.append(Ticket.created_at >= date_from)
        if date_to:
            created_filter.append(Ticket.created_at <= date_to)

        # 1. Total created tickets
        total_created_stmt = select(func.count(Ticket.id))
        if created_filter:
            total_created_stmt = total_created_stmt.where(*created_filter)
        total_created = (await self.session.execute(total_created_stmt)).scalar() or 0

        # 2. Total answered tickets (closed)
        total_answered_stmt = select(func.count(Ticket.id)).where(
            Ticket.status == TicketStatus.CLOSED
        )
        if created_filter:
            total_answered_stmt = total_answered_stmt.where(*created_filter)
        total_answered = (await self.session.execute(total_answered_stmt)).scalar() or 0

        # 3. Total overdue tickets (either currently overdue or was overdue)
        total_overdue_stmt = select(func.count(Ticket.id)).where(
            Ticket.sla_status == SLAStatus.OVERDUE
        )
        if created_filter:
            total_overdue_stmt = total_overdue_stmt.where(*created_filter)
        total_overdue = (await self.session.execute(total_overdue_stmt)).scalar() or 0

        # 4. Median first response time (seconds)
        bind = self.session.bind or self.session.get_bind()
        if bind and bind.dialect.name == "sqlite":
            # SQLite fallback for test environment
            tickets_stmt = select(Ticket.first_response_time).where(
                Ticket.status == TicketStatus.CLOSED,
                Ticket.first_response_time.isnot(None),
            )
            if created_filter:
                tickets_stmt = tickets_stmt.where(*created_filter)
            intervals = (await self.session.execute(tickets_stmt)).scalars().all()
            if intervals:
                import statistics

                seconds_list = [
                    i.total_seconds() if hasattr(i, "total_seconds") else float(i)
                    for i in intervals
                ]
                median_val = round(float(statistics.median(seconds_list)), 2)
            else:
                median_val = None
        else:
            # PostgreSQL: percentile_cont(0.5) computed directly in the database
            epoch_seconds = func.extract("epoch", Ticket.first_response_time)
            median_stmt = (
                select(
                    func.percentile_cont(0.5)
                    .within_group(epoch_seconds.asc())
                    .label("median_seconds")
                )
                .where(Ticket.status == TicketStatus.CLOSED)
                .where(Ticket.first_response_time.isnot(None))
            )
            if created_filter:
                median_stmt = median_stmt.where(*created_filter)

            median_result = (await self.session.execute(median_stmt)).scalar()
            median_val = round(float(median_result), 2) if median_result is not None else None

        return {
            "total_created": total_created,
            "total_answered": total_answered,
            "total_overdue": total_overdue,
            "median_first_response_time_seconds": median_val,
        }
