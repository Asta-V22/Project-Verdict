"""
Centralized FastAPI dependency providers.

All ``Depends()`` callables used across routers are re-exported here.
This gives a single importable location for dependency injection.

Usage in routers::

    from app.dependencies import get_db

    @router.get("/items")
    def list_items(db: Session = Depends(get_db)):
        ...

Pattern for future service injection::

    def get_task_service(db: Session = Depends(get_db)) -> TaskService:
        return TaskService(db)
"""

from app.database import get_db  # noqa: F401 — re-export for discoverability
