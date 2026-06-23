"""Routers package."""

from app.routers.categories import router as categories_router
from app.routers.health import router as health_router
from app.routers.tasks import router as tasks_router

__all__ = ["categories_router", "health_router", "tasks_router"]
