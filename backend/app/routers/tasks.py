"""
Task CRUD endpoints.

All endpoints follow the standard response envelope and use
the exception hierarchy for error handling.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.responses import SuccessResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_service(db: Session = Depends(get_db)) -> TaskService:
    return TaskService(db)


@router.post(
    "",
    response_model=SuccessResponse[TaskResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    data: TaskCreate,
    service: TaskService = Depends(_get_service),
) -> dict:
    """Create a new task."""
    task = service.create(data)
    return {"success": True, "data": TaskResponse.model_validate(task)}


@router.get("", response_model=SuccessResponse[list[TaskResponse]])
def list_tasks(
    service: TaskService = Depends(_get_service),
) -> dict:
    """List all active (non-archived) tasks."""
    tasks = service.list_active()
    return {
        "success": True,
        "data": [TaskResponse.model_validate(t) for t in tasks],
    }


@router.get("/{task_id}", response_model=SuccessResponse[TaskResponse])
def get_task(
    task_id: str,
    service: TaskService = Depends(_get_service),
) -> dict:
    """Get a single task by ID."""
    task = service.get_by_id(task_id)
    return {"success": True, "data": TaskResponse.model_validate(task)}


@router.patch("/{task_id}", response_model=SuccessResponse[TaskResponse])
def update_task(
    task_id: str,
    data: TaskUpdate,
    service: TaskService = Depends(_get_service),
) -> dict:
    """Update a task. Only provided fields are changed."""
    task = service.update(task_id, data)
    return {"success": True, "data": TaskResponse.model_validate(task)}


@router.delete("/{task_id}", response_model=SuccessResponse[TaskResponse])
def delete_task(
    task_id: str,
    service: TaskService = Depends(_get_service),
) -> dict:
    """Soft-delete (archive) a task."""
    task = service.archive(task_id)
    return {"success": True, "data": TaskResponse.model_validate(task)}
