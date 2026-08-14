"""Базовые классы и миксины для ORM-моделей SQLAlchemy.

Назначение:
- Декларативная база моделей `Base` (`DeclarativeBase`).
- Миксины для добавления временных меток (`created_at`, `updated_at`) и первичных ключей (`UUIDMixin`).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
