"""ORM-модель входящих событий (Events).

Назначение:
- Определение таблицы `events` с уникальным ограничением `UNIQUE (external_event_id)` для идемпотентности.
- Хранение полезной нагрузки (`payload` в JSONB) и метаданных события.
"""

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EventType(enum.StrEnum):
    CLIENT = "client"
    AGENT = "agent"


class Event(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "events"

    external_event_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
