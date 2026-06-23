"""
Category CRUD endpoints.

All endpoints follow the standard response envelope and use
the exception hierarchy for error handling.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.responses import SuccessResponse
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


def _get_service(db: Session = Depends(get_db)) -> CategoryService:
    return CategoryService(db)


@router.post(
    "",
    response_model=SuccessResponse[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    data: CategoryCreate,
    service: CategoryService = Depends(_get_service),
) -> dict:
    """Create a new category."""
    category = service.create(data)
    return {"success": True, "data": CategoryResponse.model_validate(category)}


@router.get("", response_model=SuccessResponse[list[CategoryResponse]])
def list_categories(
    service: CategoryService = Depends(_get_service),
) -> dict:
    """List all active (non-archived) categories."""
    categories = service.list_active()
    return {
        "success": True,
        "data": [CategoryResponse.model_validate(c) for c in categories],
    }


@router.get("/{category_id}", response_model=SuccessResponse[CategoryResponse])
def get_category(
    category_id: str,
    service: CategoryService = Depends(_get_service),
) -> dict:
    """Get a single category by ID."""
    category = service.get_by_id(category_id)
    return {"success": True, "data": CategoryResponse.model_validate(category)}


@router.patch("/{category_id}", response_model=SuccessResponse[CategoryResponse])
def update_category(
    category_id: str,
    data: CategoryUpdate,
    service: CategoryService = Depends(_get_service),
) -> dict:
    """Update a category. Only provided fields are changed."""
    category = service.update(category_id, data)
    return {"success": True, "data": CategoryResponse.model_validate(category)}


@router.delete("/{category_id}", response_model=SuccessResponse[CategoryResponse])
def delete_category(
    category_id: str,
    service: CategoryService = Depends(_get_service),
) -> dict:
    """Soft-delete (archive) a category."""
    category = service.archive(category_id)
    return {"success": True, "data": CategoryResponse.model_validate(category)}
