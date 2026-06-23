"""
APScheduler lifecycle management.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.jobs.reminders import check_due_reminders

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler()

# Flag to prevent double-starts during dev reloads or if multiple lifespan events occur
_is_started = False


def start_scheduler() -> None:
    """Configure and start the background scheduler exactly once."""
    global _is_started
    if _is_started:
        return

    logger.info("Initializing APScheduler...")

    # Add the reminder check job to run at the start of every minute
    scheduler.add_job(
        check_due_reminders,
        trigger="cron",
        minute="*",
        id="check_due_reminders",
        replace_existing=True,
    )

    scheduler.start()
    _is_started = True
    logger.info("APScheduler started successfully.")


def stop_scheduler() -> None:
    """Gracefully shutdown the scheduler."""
    global _is_started
    if _is_started:
        logger.info("Shutting down APScheduler...")
        scheduler.shutdown(wait=False)
        _is_started = False
