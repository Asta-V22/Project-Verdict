"""
Reminders API endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.reminder import ReminderCreate, ReminderResponse, ReminderUpdate
from app.schemas.responses import SuccessResponse, success
from app.services.reminder_service import ReminderService

router = APIRouter(tags=["reminders"])


def _get_reminder_service(db: Session = Depends(get_db)) -> ReminderService:
    return ReminderService(db)


@router.post("/reminders", response_model=SuccessResponse[ReminderResponse], status_code=201)
def create_reminder(
    data: ReminderCreate,
    service: ReminderService = Depends(_get_reminder_service),
) -> dict:
    """Create a new reminder."""
    reminder = service.create_reminder(data)
    return success(ReminderResponse.model_validate(reminder))


@router.get("/reminders", response_model=SuccessResponse[list[ReminderResponse]])
def list_reminders(
    service: ReminderService = Depends(_get_reminder_service),
) -> dict:
    """List all reminders."""
    reminders = service.list_all()
    return success([ReminderResponse.model_validate(r) for r in reminders])


@router.get("/reminders/{reminder_id}", response_model=SuccessResponse[ReminderResponse])
def get_reminder(
    reminder_id: str,
    service: ReminderService = Depends(_get_reminder_service),
) -> dict:
    """Get a single reminder by ID."""
    reminder = service.get_reminder(reminder_id)
    return success(ReminderResponse.model_validate(reminder))


@router.get("/tasks/{task_id}/reminders", response_model=SuccessResponse[list[ReminderResponse]])
def get_task_reminders(
    task_id: str,
    service: ReminderService = Depends(_get_reminder_service),
) -> dict:
    """List reminders for a specific task."""
    reminders = service.get_by_task(task_id)
    return success([ReminderResponse.model_validate(r) for r in reminders])


@router.patch("/reminders/{reminder_id}", response_model=SuccessResponse[ReminderResponse])
def update_reminder(
    reminder_id: str,
    data: ReminderUpdate,
    service: ReminderService = Depends(_get_reminder_service),
) -> dict:
    """Update a reminder."""
    reminder = service.update_reminder(reminder_id, data)
    return success(ReminderResponse.model_validate(reminder))


@router.delete("/reminders/{reminder_id}", status_code=204)
def delete_reminder(
    reminder_id: str,
    service: ReminderService = Depends(_get_reminder_service),
) -> None:
    """Permanently delete a reminder."""
    service.delete_reminder(reminder_id)
