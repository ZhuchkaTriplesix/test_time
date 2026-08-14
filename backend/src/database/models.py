"""Централизованный реестр ORM-моделей базы данных.

Назначение:
- Реэкспорт базового класса `Base` и всех моделей доменов (`Ticket`, `Event`, `OutboxEvent`).
- Используется Alembic (`env.py`) для автоматического обнаружения таблиц и генерации миграций.
"""

from src.database.base import Base
from src.routers.events.models import Event, EventType
from src.routers.outbox.models import OutboxEvent, OutboxStatus
from src.routers.tickets.models import SLAStatus, Ticket, TicketStatus

__all__ = [
    "Base",
    "Ticket",
    "TicketStatus",
    "SLAStatus",
    "Event",
    "EventType",
    "OutboxEvent",
    "OutboxStatus",
]
