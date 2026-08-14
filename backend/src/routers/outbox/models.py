import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now


class OutboxStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class OutboxEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "outbox_events"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    status: Mapped[OutboxStatus] = mapped_column(
        Enum(OutboxStatus, name="outbox_status", values_callable=lambda x: [e.value for e in x]),
        default=OutboxStatus.PENDING,
        nullable=False,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (Index("ix_outbox_status_available_at", "status", "available_at"),)
