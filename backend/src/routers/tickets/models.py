"""ORM-модель обращений (Tickets) и статусы SLA.

Назначение:
- Определение перечислений `TicketStatus` (`open`, `closed`) и `SLAStatus` (`normal`, `warning`, `overdue`).
- Определение таблицы `tickets` с индексами по статусу, топику и датам создания/ответа.
"""

import enum
from datetime import datetime, timedelta

from sqlalchemy import DateTime, Enum, Index, Interval, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TicketStatus(enum.StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class SLAStatus(enum.StrEnum):
    NORMAL = "normal"
    WARNING = "warning"
    OVERDUE = "overdue"


class Ticket(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tickets"

    external_client_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    topic: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status", values_callable=lambda x: [e.value for e in x]),
        default=TicketStatus.OPEN,
        nullable=False,
        index=True,
    )
    sla_status: Mapped[SLAStatus] = mapped_column(
        Enum(SLAStatus, name="sla_status", values_callable=lambda x: [e.value for e in x]),
        default=SLAStatus.NORMAL,
        nullable=False,
        index=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    first_response_time: Mapped[timedelta | None] = mapped_column(
        Interval,
        nullable=True,
    )

    __table_args__ = (
        Index("ix_tickets_status_topic", "status", "topic"),
        Index("ix_tickets_status_created_at", "status", "created_at"),
    )
