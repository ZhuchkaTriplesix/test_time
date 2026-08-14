import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from src.config import get_settings
from src.database.core import close_db_engine, get_db_engine
from src.middlewares import LoggingAndErrorMiddleware
from src.routers import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown."""
    # Startup: ensure db engine is initialized
    get_db_engine()
    logger.info("FastAPI application started. Database engine initialized.")
    yield
    # Shutdown: cleanly dispose db pool
    await close_db_engine()
    logger.info("FastAPI application shutdown. Database connections closed.")


class App:
    """FastAPI Application factory class."""

    def __init__(self):
        settings = get_settings()
        self._app = FastAPI(
            title=settings.APP_NAME,
            version=settings.APP_VERSION,
            description="Service for tracking customer ticket first response times, SLA breaches and analytics.",
            default_response_class=ORJSONResponse,
            lifespan=lifespan,
        )
        self._configure_middlewares()
        self._configure_routes()

    def _configure_middlewares(self) -> None:
        # 1. CORS Middleware
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        # 2. Custom Logging and Timing Middleware
        self._app.add_middleware(LoggingAndErrorMiddleware)

    def _configure_routes(self) -> None:
        self._app.include_router(api_router)

    @property
    def app(self) -> FastAPI:
        return self._app
