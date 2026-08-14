"""Модуль конфигурации приложения (Pydantic Settings).

Назначение:
- Централизованное управление переменными окружения и настройками проекта.
- Загрузка параметров подключения к PostgreSQL, порогов SLA (warning/overdue),
  таймаутов воркера и параметров логирования из файла .env.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database connection parameters
    DATABASE_URL: str | None = None
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "tickets_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Database Pool Settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False

    # SLA Thresholds (in seconds)
    SLA_WARNING_SECONDS: int = Field(default=60, description="Seconds before ticket SLA warning")
    SLA_OVERDUE_SECONDS: int = Field(default=180, description="Seconds before ticket SLA overdue")

    # Worker & Sweeper intervals
    WORKER_POLL_INTERVAL_SECONDS: float = 2.0
    SLA_SWEEPER_INTERVAL_SECONDS: float = 5.0
    NOTIFICATION_DELAY_SECONDS: float = 0.0

    # Server settings
    API_PORT: int = 8000
    APP_NAME: str = "SLA Ticket Response Time Control Service"
    APP_VERSION: str = "1.0.0"

    def get_database_url(self) -> str:
        """Return the async database connection URL."""
        if self.DATABASE_URL:
            # Ensure asyncpg driver is specified
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
