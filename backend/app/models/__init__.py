"""
Models package — re-exports all ORM models and the declarative Base.

Importing this package ensures all models are registered with SQLAlchemy's
metadata, which is required for `Base.metadata.create_all()` and Alembic
auto-generation to discover all tables.
"""

from app.models.app_state import AppState
from app.models.base import Base
from app.models.category import Category
from app.models.daily_verdict import DailyVerdict
from app.models.evidence import Evidence
from app.models.reminder import Reminder
from app.models.task import Task
from app.models.task_instance import TaskInstance
from app.models.task_metrics import TaskMetrics

__all__ = [
    "AppState",
    "Base",
    "Category",
    "DailyVerdict",
    "Evidence",
    "Reminder",
    "Task",
    "TaskInstance",
    "TaskMetrics",
]
