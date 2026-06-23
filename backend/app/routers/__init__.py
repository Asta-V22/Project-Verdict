"""Routers package."""

from .categories import router as categories_router
from .evidence import router as evidence_router
from .health import router as health_router
from .instances import router as instances_router
from .reminders import router as reminders_router
from .tasks import router as tasks_router

__all__ = [
    "categories_router",
    "evidence_router",
    "health_router",
    "instances_router",
    "reminders_router",
    "tasks_router",
]
