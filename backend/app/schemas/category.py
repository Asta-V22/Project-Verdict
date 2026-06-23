"""
Pydantic schemas for Category CRUD operations.

Schemas:
  CategoryCreate  — POST body
  CategoryUpdate  — PATCH body (all fields optional)
  CategoryResponse — serialized output for API responses
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, field_validator


class CategoryCreate(BaseModel):
    """Schema for creating a new category."""

    name: str
    color: str  # Hex color, e.g. "#FF5733"
    icon: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Category name must not be empty")
        if len(v) > 100:
            raise ValueError("Category name must be 100 characters or fewer")
        return v

    @field_validator("color")
    @classmethod
    def valid_hex_color(cls, v: str) -> str:
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Color must be a valid hex color (e.g. #FF5733)")
        return v.upper()


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category. All fields are optional."""

    name: str | None = None
    color: str | None = None
    icon: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Category name must not be empty")
            if len(v) > 100:
                raise ValueError("Category name must be 100 characters or fewer")
        return v

    @field_validator("color")
    @classmethod
    def valid_hex_color(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Color must be a valid hex color (e.g. #FF5733)")
        return v.upper() if v else v


class CategoryResponse(BaseModel):
    """Serialized category for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    color: str
    icon: str | None
    is_active: bool
    created_at: str

    @field_validator("created_at", mode="before")
    @classmethod
    def serialize_datetime(cls, v):
        """Convert datetime to ISO string if it's a datetime object."""
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return v
