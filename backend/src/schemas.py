"""Базовые схемы Pydantic для всего приложения.

Назначение:
- Определение базовых классов моделей с общей конфигурацией сериализации.
- Определение универсальных схем ответов (статус операции, пагинация, ошибки).
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class GenericResponse(BaseSchema, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None


class ErrorResponse(BaseSchema):
    success: bool = False
    error: str
    detail: str | None = None
