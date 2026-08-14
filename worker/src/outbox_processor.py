import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_worker_settings
from src.database import get_session_factory
from src.models import OutboxEvent, OutboxStatus
from src.notifications import get_notification_adapter

logger = logging.getLogger(__name__)


async def process_outbox_batch(session: AsyncSession) -> int:
    """Select and deliver pending outbox events using SKIP LOCKED locks."""
    settings = get_worker_settings()
    adapter = get_notification_adapter()
    now = datetime.now(UTC)

    processed_count = 0

    async with session.begin():
        # Select pending events with FOR UPDATE SKIP LOCKED
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxStatus.PENDING)
            .where(OutboxEvent.available_at <= now)
            .order_by(OutboxEvent.created_at.asc())
            .limit(settings.OUTBOX_BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )
        events = (await session.execute(stmt)).scalars().all()

        for event in events:
            payload = event.payload
            try:
                # Deliver alert via non-blocking adapter
                delivered = await adapter.send_alert(
                    topic=payload.get("topic", "General"),
                    ticket_id=payload.get("ticket_id", str(event.ticket_id)),
                    sla_status=payload.get("sla_status", "warning"),
                    wait_time_seconds=payload.get("wait_time_seconds", 0.0),
                    content=payload.get("content", ""),
                    extra=payload,
                )
                if delivered:
                    event.status = OutboxStatus.DONE
                    processed_count += 1
                else:
                    raise RuntimeError("Adapter reported failure to deliver alert")

            except Exception as e:
                event.attempts += 1
                event.last_error = str(e)
                if event.attempts >= settings.OUTBOX_MAX_ATTEMPTS:
                    event.status = OutboxStatus.FAILED
                    logger.error(
                        "Outbox event %s failed permanently after %d attempts: %s",
                        event.id,
                        event.attempts,
                        e,
                    )
                else:
                    # Exponential backoff retry
                    retry_delay = 2**event.attempts
                    event.available_at = now + timedelta(seconds=retry_delay)
                    logger.warning(
                        "Outbox event %s attempt %d failed (%s). Retrying in %ds.",
                        event.id,
                        event.attempts,
                        e,
                        retry_delay,
                    )

    return processed_count


async def outbox_processor_loop() -> None:
    """Continuous outbox background delivery processor loop."""
    settings = get_worker_settings()
    session_factory = get_session_factory()
    logger.info(
        "Outbox Processor started (poll_interval=%.1fs, batch_size=%d)",
        settings.WORKER_POLL_INTERVAL_SECONDS,
        settings.OUTBOX_BATCH_SIZE,
    )

    while True:
        try:
            async with session_factory() as session:
                processed = await process_outbox_batch(session)
                # If we processed a full batch, quickly check for more without sleeping
                if processed >= settings.OUTBOX_BATCH_SIZE:
                    continue
        except asyncio.CancelledError:
            logger.info("Outbox Processor loop received cancellation.")
            break
        except Exception:
            logger.exception("Error in Outbox Processor cycle:")

        await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
