"""
Notification service — resolves reminders against pending tasks and dispatches.
"""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.core.notifications import NotificationProvider
from app.models.enums import InstanceStatus
from app.models.reminder import Reminder
from app.repositories.task_instance import TaskInstanceRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """Orchestrates evaluating reminders and pushing notifications."""

    def __init__(self, db: Session, provider: NotificationProvider) -> None:
        self.db = db
        self.provider = provider
        self.instance_repo = TaskInstanceRepository(db)

    def dispatch_reminders(self, reminders: list[Reminder]) -> None:
        """
        Given a list of due reminders, resolve their targets.
        If global -> check if ANY pending tasks exist today.
        If task-specific -> check if THAT task has a pending instance today.
        Send notifications to the configured provider.
        """
        today = date.today()
        # Cache today's pending instances to avoid N+1 queries if there are many reminders
        pending_instances = self.instance_repo.get_all(
            instance_date=today, status=InstanceStatus.PENDING.value
        )

        if not pending_instances:
            logger.info("No pending tasks today. Skipping all reminders.")
            return

        # Map task_id -> Instance for quick lookup
        pending_map = {inst.task_id: inst for inst in pending_instances}
        global_sent = False

        for reminder in reminders:
            if not reminder.task_id:
                # Global reminder
                if pending_instances and not global_sent:
                    count = len(pending_instances)
                    title = "Project Verdict"
                    msg = (
                        f"You have {count} pending task{'s' if count > 1 else ''} "
                        "to complete today."
                    )
                    self.provider.send_notification(title, msg, reminder.urgency_level)
                    global_sent = True
            else:
                # Task-specific reminder
                instance = pending_map.get(reminder.task_id)
                if instance and instance.task and instance.task.is_active:
                    title = "Task Reminder"
                    msg = f"Don't forget: {instance.task.title}"
                    self.provider.send_notification(title, msg, reminder.urgency_level)
