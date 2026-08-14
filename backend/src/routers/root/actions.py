"""Бизнес-логика системных проверок доступности сервиса.

Назначение:
- Выполнение тестового запроса к СУБД для подтверждения работоспособности соединения.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.routers.root.schemas import HealthResponse


async def check_health(session: AsyncSession) -> HealthResponse:
    """Validate database connectivity and service readiness."""
    settings = get_settings()
    try:
        await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"

    overall_status = "ok" if db_status == "connected" else "degraded"
    return HealthResponse(
        status=overall_status,
        database=db_status,
        version=settings.APP_VERSION,
    )
