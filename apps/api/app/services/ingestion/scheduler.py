"""APScheduler-based ingestion scheduler."""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_scheduler = AsyncIOScheduler()


async def _run():
    from app.services.ingestion.pipeline import run_all_sources
    await run_all_sources()


def start_scheduler():
    _scheduler.add_job(
        _run,
        trigger=IntervalTrigger(minutes=settings.ingestion_interval_minutes),
        id="ingestion",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info(f"Ingestion scheduler started (every {settings.ingestion_interval_minutes} min)")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)


async def run_ingestion_now():
    """Trigger immediate ingestion (used from admin endpoint)."""
    await _run()
