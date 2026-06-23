"""
APScheduler job orchestrator for Reminders.
"""

from __future__ import annotations

import logging

from app.core.notifications import DesktopNotificationProvider
from app.database import SessionLocal
from app.services.notification_service import NotificationService
from app.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)


def check_due_reminders() -> None:
    """
    Cron job triggered every minute by APScheduler.
    Instantiates its own DB session, fetches due reminders,
    and dispatches them.
    """
    logger.debug("Running check_due_reminders cron job...")

    db = SessionLocal()
    try:
        reminder_service = ReminderService(db)
        provider = DesktopNotificationProvider()
        notification_service = NotificationService(db, provider)

        due_reminders = reminder_service.get_due_reminders()
        if not due_reminders:
            return

        logger.info("Found %d due reminder(s). Dispatching...", len(due_reminders))
        notification_service.dispatch_reminders(due_reminders)

    except Exception:
        logger.exception("Error executing check_due_reminders job")
    finally:
        db.close()
