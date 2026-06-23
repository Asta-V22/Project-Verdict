"""
TaskInstance and Generation endpoints.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.responses import SuccessResponse
from app.schemas.task_instance import (
    SyncInstancesResponse,
    TaskInstanceResponse,
    TaskInstanceUpdate,
)
from app.services.generation_service import GenerationService
from app.services.task_instance_service import TaskInstanceService

router = APIRouter(tags=["instances"])


def _get_instance_service(db: Session = Depends(get_db)) -> TaskInstanceService:
    return TaskInstanceService(db)


def _get_generation_service(db: Session = Depends(get_db)) -> GenerationService:
    return GenerationService(db)


@router.post(
    "/sync/instances",
    response_model=SuccessResponse[SyncInstancesResponse],
)
def sync_instances(
    service: GenerationService = Depends(_get_generation_service),
) -> dict:
    """
    Trigger the instance generation engine up to the current date.

    This evaluates all active recurring tasks and backfills any missing
    instances since the last sync. It respects MAX_BACKFILL_DAYS.
    """
    result = service.sync_instances()
    return {"success": True, "data": result}


@router.get(
    "/instances",
    response_model=SuccessResponse[list[TaskInstanceResponse]],
)
def list_instances(
    target_date: date = Query(..., description="The date to fetch instances for (YYYY-MM-DD)"),
    service: TaskInstanceService = Depends(_get_instance_service),
) -> dict:
    """Fetch all task instances for a specific date."""
    instances = service.get_by_date(target_date)
    return {
        "success": True,
        "data": [TaskInstanceResponse.model_validate(inst) for inst in instances],
    }


@router.get(
    "/instances/{instance_id}",
    response_model=SuccessResponse[TaskInstanceResponse],
)
def get_instance(
    instance_id: str,
    service: TaskInstanceService = Depends(_get_instance_service),
) -> dict:
    """Get a single task instance by ID."""
    instance = service.get_by_id(instance_id)
    return {"success": True, "data": TaskInstanceResponse.model_validate(instance)}


@router.patch(
    "/instances/{instance_id}/status",
    response_model=SuccessResponse[TaskInstanceResponse],
)
def update_instance_status(
    instance_id: str,
    data: TaskInstanceUpdate,
    service: TaskInstanceService = Depends(_get_instance_service),
) -> dict:
    """Update the status of a specific instance (e.g. mark as skipped)."""
    instance = service.update_status(instance_id, data)
    return {"success": True, "data": TaskInstanceResponse.model_validate(instance)}
