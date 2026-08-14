from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import get_db
from src.routers.metrics.actions import compute_metrics
from src.routers.metrics.schemas import MetricsResponse

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])


@router.get(
    "",
    response_model=MetricsResponse,
    summary="Get operational SLA metrics and median response time",
    description="Returns aggregate metrics: total created, total answered, total overdue, and continuous median response time in seconds.",
)
async def get_metrics(
    date_from: datetime | None = Query(
        default=None, description="Start of period filter (ISO 8601)"
    ),
    date_to: datetime | None = Query(default=None, description="End of period filter (ISO 8601)"),
    session: AsyncSession = Depends(get_db),
):
    return await compute_metrics(session=session, date_from=date_from, date_to=date_to)
