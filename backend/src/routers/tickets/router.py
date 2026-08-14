"""HTTP-маршрутизатор для чтения и фильтрации обращений (`GET /api/tickets`).

Назначение:
- Получение списка открытых обращений с опциональной фильтрацией по направлению (`topic`).
- Предоставление актуального списка доступных тематик для UI-фильтров.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import get_db
from src.routers.tickets.actions import list_open_tickets
from src.routers.tickets.schemas import TicketListResponse

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


@router.get(
    "",
    response_model=TicketListResponse,
    summary="List open tickets with dynamic wait times and SLA",
    description="Returns all currently open tickets with computed wait time and SLA status. Supports optional topic filtering.",
)
async def get_tickets(
    topic: str | None = Query(default=None, description="Filter tickets by topic/department"),
    session: AsyncSession = Depends(get_db),
):
    return await list_open_tickets(session=session, topic=topic)
