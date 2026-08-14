from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.metrics.dal import MetricsDAL
from src.routers.metrics.schemas import MetricsResponse


async def compute_metrics(
    session: AsyncSession,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> MetricsResponse:
    """Compute and return operational metrics for the period."""
    dal = MetricsDAL(session)
    data = await dal.get_metrics(date_from=date_from, date_to=date_to)

    return MetricsResponse(
        total_created=data["total_created"],
        total_answered=data["total_answered"],
        total_overdue=data["total_overdue"],
        median_first_response_time_seconds=data["median_first_response_time_seconds"],
        period_from=date_from,
        period_to=date_to,
    )
