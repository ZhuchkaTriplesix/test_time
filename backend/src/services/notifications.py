import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from src.config import get_settings

logger = logging.getLogger(__name__)


class NotificationAdapter(ABC):
    """Abstract interface for external notification delivery."""

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
        """Deliver alert to external communication channel."""
        pass


class LocalLogNotificationAdapter(NotificationAdapter):
    """Local simulation adapter that logs alerts and optionally simulates network delay."""

    def __init__(self, delay_seconds: float | None = None):
        settings = get_settings()
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
        # Non-blocking asynchronous simulation delay (for testing non-blocking concurrency)
        if self.delay_seconds > 0:
            logger.info(
                "[NotificationAdapter] Simulating network call delay of %.2fs...",
                self.delay_seconds,
            )
            await asyncio.sleep(self.delay_seconds)

        logger.info(
            "📢 [SLA ALERT SENT] -> Topic: '%s' | Ticket: %s | Status: %s | Wait Time: %.1fs | Message: '%s'",
            topic,
            ticket_id,
            sla_status.upper(),
            wait_time_seconds,
            content[:100] + ("..." if len(content) > 100 else ""),
        )
        return True


# Global default adapter instance
_default_adapter: NotificationAdapter | None = None


def get_notification_adapter() -> NotificationAdapter:
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = LocalLogNotificationAdapter()
    return _default_adapter


def set_notification_adapter(adapter: NotificationAdapter) -> None:
    global _default_adapter
    _default_adapter = adapter
