"""HTTP-маршрутизатор приема входящих событий (`POST /api/events`).

Назначение:
- Прием клиентских обращений и ответов сотрудников.
- Атомарное выполнение бизнес-логики внутри транзакции.
- Возврат `201 Created` для новых событий и `200 OK` для дубликатов (идемпотентность).
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import get_db
from src.routers.events.actions import ingest_event
from src.routers.events.schemas import EventIngestRequest, EventIngestResponse

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.post(
    "",
    response_model=EventIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest external client or agent event",
    description=(
        "Accepts incoming client or agent events with strict idempotency (ON CONFLICT DO NOTHING). "
        "Returns 201 Created for new events and 200 OK for duplicates."
    ),
)
async def handle_event(
    event_data: EventIngestRequest,
    session: AsyncSession = Depends(get_db),
):
    if session.in_transaction():
        async with session.begin_nested():
            response_data, is_created = await ingest_event(event_data, session)
    else:
        async with session.begin():
            response_data, is_created = await ingest_event(event_data, session)

    status_code = status.HTTP_201_CREATED if is_created else status.HTTP_200_OK
    return JSONResponse(
        status_code=status_code,
        content=response_data.model_dump(mode="json"),
    )
