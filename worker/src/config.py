"""Конфигурация фонового воркера (Pydantic Settings).

Назначение:
- Загрузка настроек подключения к PostgreSQL, интервалов свипера SLA (warning/overdue),
  батчинга Outbox и параметров экспоненциального retry из переменных окружения.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str | None = None
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "tickets_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Database Pool Settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # SLA Thresholds (in seconds)
    SLA_WARNING_SECONDS: int = Field(default=60, description="Seconds before ticket SLA warning")
    SLA_OVERDUE_SECONDS: int = Field(default=180, description="Seconds before ticket SLA overdue")

    # Loop Intervals (in seconds)
    WORKER_POLL_INTERVAL_SECONDS: float = 2.0
    SLA_SWEEPER_INTERVAL_SECONDS: float = 5.0
    NOTIFICATION_DELAY_SECONDS: float = 0.0

    # Outbox configuration
    OUTBOX_BATCH_SIZE: int = 10
    OUTBOX_MAX_ATTEMPTS: int = 5

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
