"""Точка входа фонового демона обработки SLA и Outbox.

Назначение:
- Параллельный запуск двух фоновых корутин: `run_sla_sweeper` и `run_outbox_processor`.
- Обработка сигналов завершения ОС (`SIGINT`, `SIGTERM`) для безопасного Graceful Shutdown.
"""

import asyncio
import contextlib
import logging
import signal

from src.database import close_db_engine, get_db_engine
from src.outbox_processor import outbox_processor_loop
from src.sla_sweeper import sla_sweeper_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("worker")


async def main() -> None:
    # Initialize database engine
    get_db_engine()
    logger.info("Worker started: initializing SLA Sweeper and Outbox Processor tasks.")

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _signal_handler():
        logger.info("Received termination signal. Initiating graceful shutdown...")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _signal_handler)

    # Launch background tasks
    sweeper_task = asyncio.create_task(sla_sweeper_loop(), name="sla_sweeper")
    outbox_task = asyncio.create_task(outbox_processor_loop(), name="outbox_processor")

    try:
        await stop_event.wait()
    finally:
        logger.info("Cancelling background tasks...")
        sweeper_task.cancel()
        outbox_task.cancel()
        await asyncio.gather(sweeper_task, outbox_task, return_exceptions=True)
        await close_db_engine()
        logger.info("Worker shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
