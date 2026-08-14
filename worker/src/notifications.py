import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from src.config import get_worker_settings

logger = logging.getLogger(__name__)


class NotificationAdapter(ABC):
    @abstractmethod
    async def send_alert(
        self,
        topic: str,
        ticket_id: str,
        sla_status: str,
        wait_time_seconds: float,
        content: str,
        extra: dict[str, Any] | None = None,
    ) -> bool:
        pass


class LocalLogNotificationAdapter(NotificationAdapter):
    def __init__(self, delay_seconds: float | None = None):
        settings = get_worker_settings()
        self.delay_seconds = (
            delay_seconds if delay_seconds is not None else settings.NOTIFICATION_DELAY_SECONDS
        )

    async def send_alert(
        self,
        topic: str,
        ticket_id: str,
        sla_status: str,
        wait_time_seconds: float,
        content: str,
        extra: dict[str, Any] | None = None,
    ) -> bool:
        if self.delay_seconds > 0:
            logger.info(
                "[Worker NotificationAdapter] Simulating delay of %.2fs...",
                self.delay_seconds,
            )
            await asyncio.sleep(self.delay_seconds)

        logger.info(
            "📢 [WORKER ALERT SENT] -> Topic: '%s' | Ticket: %s | SLA: %s | Wait Time: %.1fs | Message: '%s'",
            topic,
            ticket_id,
            sla_status.upper(),
            wait_time_seconds,
            content[:100] + ("..." if len(content) > 100 else ""),
        )
        return True


_default_adapter: NotificationAdapter | None = None


def get_notification_adapter() -> NotificationAdapter:
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = LocalLogNotificationAdapter()
    return _default_adapter


def set_notification_adapter(adapter: NotificationAdapter) -> None:
    global _default_adapter
    _default_adapter = adapter
