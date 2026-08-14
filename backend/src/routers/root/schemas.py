"""Pydantic-схемы для системного эндпоинта Health Check.

Назначение:
- Описание структуры ответа `HealthCheckResponse` (статус API и доступность БД).
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str
