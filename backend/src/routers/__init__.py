from fastapi import APIRouter

from src.routers.events.router import router as events_router
from src.routers.metrics.router import router as metrics_router
from src.routers.root.router import router as root_router
from src.routers.tickets.router import router as tickets_router

api_router = APIRouter()

# Register sub-routers
api_router.include_router(root_router)
api_router.include_router(events_router)
api_router.include_router(tickets_router)
api_router.include_router(metrics_router)

__all__ = ["api_router"]
