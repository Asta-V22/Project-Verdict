"""
Standard API response schemas.

Every endpoint returns one of two shapes:

  Success: {"success": true,  "data": <T>}
  Error:   {"success": false, "error": {"code": str, "message": str, "details": [...]}}

This module defines the Pydantic models for both, plus a helper function
for building success responses concisely.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


# ── Error envelope ────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    """A single validation error or sub-error."""

    field: str | None = None
    message: str


class ErrorBody(BaseModel):
    """Error payload inside an error response."""

    code: str
    message: str
    details: list[ErrorDetail] = []


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    success: bool = False
    error: ErrorBody


# ── Success envelope ──────────────────────────────────────────────────

class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response envelope wrapping arbitrary data."""

    success: bool = True
    data: T


# ── Concrete response data models ────────────────────────────────────

class HealthData(BaseModel):
    """Data payload for the health endpoint."""

    status: str
    app: str
    version: str
    database: str
    db_path: str
    evidence_dir: str
    max_evidence_file_size_mb: int
    timestamp: str


# ── Helper ────────────────────────────────────────────────────────────

def success(data: Any) -> dict:
    """Wrap data in a success envelope dict. Convenience for simple routes."""
    return {"success": True, "data": data}
