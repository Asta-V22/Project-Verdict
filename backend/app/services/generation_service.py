"""
Generation Service — the engine that converts Tasks into daily TaskInstances.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import RecurrenceType
from app.models.task import Task
from app.models.task_instance import TaskInstance
from app.repositories.app_state import AppStateRepository
from app.repositories.task import TaskRepository
from app.repositories.task_instance import TaskInstanceRepository

logger = logging.getLogger(__name__)

LAST_SYNC_KEY = "last_instance_sync_date"


class GenerationService:
    """Engine responsible for backfilling and generating daily obligations."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.task_repo = TaskRepository(db)
        self.instance_repo = TaskInstanceRepository(db)
        self.state_repo = AppStateRepository(db)

    def _evaluate_recurrence(self, task: Task, target_date: date) -> bool:
        """Determine if a task should have an instance on the given date."""
        if task.recurrence == RecurrenceType.NONE.value:
            return False

        if task.recurrence == RecurrenceType.DAILY.value:
            return True

        weekday = target_date.weekday()  # 0=Mon, 6=Sun

        if task.recurrence == RecurrenceType.WEEKDAYS.value:
            return weekday < 5  # Mon-Fri

        if task.recurrence == RecurrenceType.CUSTOM.value:
            if not task.recurrence_days:
                return False
            try:
                days = json.loads(task.recurrence_days)
                return weekday in days
            except json.JSONDecodeError:
                logger.error("Invalid recurrence_days JSON for task %s", task.id)
                return False

        return False

    def sync_instances(self) -> dict[str, int | str | bool]:
        """
        Trigger generation up to the current date.
        Returns a dict with generated count and truncation flag.
        """
        today = datetime.now().date()

        # 1. Determine sync range
        last_sync_str = self.state_repo.get_value(LAST_SYNC_KEY)

        if last_sync_str:
            last_sync_date = date.fromisoformat(last_sync_str)
            # If already synced today, nothing to do
            if last_sync_date >= today:
                return {
                    "generated_count": 0,
                    "synced_up_to": today.isoformat(),
                    "truncation_occurred": False,
                }
            start_date = last_sync_date + timedelta(days=1)
        else:
            # First time running, just generate for today
            start_date = today

        # 2. Check backfill limits
        truncation_occurred = False
        days_to_sync = (today - start_date).days + 1

        if days_to_sync > settings.max_backfill_days:
            start_date = today - timedelta(days=settings.max_backfill_days - 1)
            truncation_occurred = True
            logger.warning(
                "Sync gap exceeded %d days. Truncating start_date to %s",
                settings.max_backfill_days, start_date
            )

        # 3. Fetch data
        active_tasks = self.task_repo.get_active()
        if not active_tasks:
            self.state_repo.set_value(LAST_SYNC_KEY, today.isoformat())
            self.db.commit()
            return {
                "generated_count": 0,
                "synced_up_to": today.isoformat(),
                "truncation_occurred": truncation_occurred,
            }

        task_ids = [t.id for t in active_tasks]
        existing_instances = self.instance_repo.get_by_task_and_date_range(
            task_ids, start_date, today
        )

        # Build lookup set: "task_id:YYYY-MM-DD"
        existing_keys = {
            f"{inst.task_id}:{inst.instance_date.isoformat()}"
            for inst in existing_instances
        }

        # 4. Generate
        new_instances = []
        current_date = start_date

        while current_date <= today:
            for task in active_tasks:
                if self._evaluate_recurrence(task, current_date):
                    key = f"{task.id}:{current_date.isoformat()}"
                    if key not in existing_keys:
                        # Copy due_time snapshot from parent
                        instance = TaskInstance(
                            task_id=task.id,
                            instance_date=current_date,
                            due_time=task.due_time,
                        )
                        new_instances.append(instance)
                        # Add to lookup to prevent dupes in same run
                        existing_keys.add(key)

            current_date += timedelta(days=1)

        # 5. Save
        if new_instances:
            self.db.add_all(new_instances)

        self.state_repo.set_value(LAST_SYNC_KEY, today.isoformat())
        self.db.commit()

        logger.info("Generated %d instances up to %s", len(new_instances), today)

        return {
            "generated_count": len(new_instances),
            "synced_up_to": today.isoformat(),
            "truncation_occurred": truncation_occurred,
        }
