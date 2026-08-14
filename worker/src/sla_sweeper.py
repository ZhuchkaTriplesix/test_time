import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_worker_settings
from src.database import get_session_factory
from src.models import OutboxEvent, OutboxStatus, SLAStatus, Ticket, TicketStatus

logger = logging.getLogger(__name__)


async def run_sla_sweep_cycle(session: AsyncSession) -> int:
    """Execute one SLA sweep cycle to transition breached tickets and enqueue alerts.

    Returns the number of status transitions processed.
    """
    settings = get_worker_settings()
    now = datetime.now(UTC)
    warning_cutoff = now - timedelta(seconds=settings.SLA_WARNING_SECONDS)
    overdue_cutoff = now - timedelta(seconds=settings.SLA_OVERDUE_SECONDS)

    transitions_count = 0

    async with session.begin():
        # 1. Detect tickets that breached OVERDUE threshold (status in normal, warning)
        overdue_stmt = (
            select(Ticket)
            .where(Ticket.status == TicketStatus.OPEN)
            .where(Ticket.sla_status.in_([SLAStatus.NORMAL, SLAStatus.WARNING]))
            .where(Ticket.created_at <= overdue_cutoff)
            .with_for_update(skip_locked=True)
        )
        overdue_tickets = (await session.execute(overdue_stmt)).scalars().all()

        for ticket in overdue_tickets:
            ticket.sla_status = SLAStatus.OVERDUE
            wait_time = (now - ticket.created_at).total_seconds()

            outbox_entry = OutboxEvent(
                id=uuid.uuid4(),
                ticket_id=ticket.id,
                event_type="sla_overdue",
                payload={
                    "topic": ticket.topic,
                    "ticket_id": str(ticket.id),
                    "sla_status": "overdue",
                    "wait_time_seconds": round(wait_time, 1),
                    "content": ticket.content,
                    "client_id": ticket.external_client_id,
                },
                status=OutboxStatus.PENDING,
                available_at=now,
                created_at=now,
            )
            session.add(outbox_entry)
            transitions_count += 1
            logger.warning(
                "⚠️ Ticket %s transitioned to OVERDUE (wait: %.1fs, topic: %s)",
                ticket.id,
                wait_time,
                ticket.topic,
            )

        # 2. Detect tickets that breached WARNING threshold (status == normal only)
        warning_stmt = (
            select(Ticket)
            .where(Ticket.status == TicketStatus.OPEN)
            .where(Ticket.sla_status == SLAStatus.NORMAL)
            .where(Ticket.created_at <= warning_cutoff)
            .where(Ticket.created_at > overdue_cutoff)
            .with_for_update(skip_locked=True)
        )
        warning_tickets = (await session.execute(warning_stmt)).scalars().all()

        for ticket in warning_tickets:
            ticket.sla_status = SLAStatus.WARNING
            wait_time = (now - ticket.created_at).total_seconds()

            outbox_entry = OutboxEvent(
                id=uuid.uuid4(),
                ticket_id=ticket.id,
                event_type="sla_warning",
                payload={
                    "topic": ticket.topic,
                    "ticket_id": str(ticket.id),
                    "sla_status": "warning",
                    "wait_time_seconds": round(wait_time, 1),
                    "content": ticket.content,
                    "client_id": ticket.external_client_id,
                },
                status=OutboxStatus.PENDING,
                available_at=now,
                created_at=now,
            )
            session.add(outbox_entry)
            transitions_count += 1
            logger.info(
                "⚡ Ticket %s transitioned to WARNING (wait: %.1fs, topic: %s)",
                ticket.id,
                wait_time,
                ticket.topic,
            )

    return transitions_count


async def sla_sweeper_loop() -> None:
    """Continuous SLA Sweeper background loop."""
    settings = get_worker_settings()
    session_factory = get_session_factory()
    logger.info(
        "SLA Sweeper started (warning=%ds, overdue=%ds, interval=%.1fs)",
        settings.SLA_WARNING_SECONDS,
        settings.SLA_OVERDUE_SECONDS,
        settings.SLA_SWEEPER_INTERVAL_SECONDS,
    )

    while True:
        try:
            async with session_factory() as session:
                await run_sla_sweep_cycle(session)
        except asyncio.CancelledError:
            logger.info("SLA Sweeper loop received cancellation.")
            break
        except Exception:
            logger.exception("Error in SLA Sweeper cycle:")

        await asyncio.sleep(settings.SLA_SWEEPER_INTERVAL_SECONDS)
