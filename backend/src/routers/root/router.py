from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import get_db
from src.routers.root.actions import check_health
from src.routers.root.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness and Readiness probe",
    description="Checks the health of the application and PostgreSQL database connectivity.",
)
async def get_health(session: AsyncSession = Depends(get_db)):
    health_info = await check_health(session)
    status_code = (
        status.HTTP_200_OK if health_info.status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(status_code=status_code, content=health_info.model_dump())
