"""
Application exception hierarchy.

All custom exceptions inherit from AppError. Global exception handlers
in main.py catch these and return consistent JSON error responses.

Usage in services/routers:
    raise NotFoundError("Task", task_id)
    raise ConflictError("Category name already exists")
    raise ValidationError("Due time must be in HH:MM format")
"""

from __future__ import annotations


class AppError(Exception):
    """Base exception for all application-level errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: list[dict] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found",
            code="NOT_FOUND",
            status_code=404,
        )


class ConflictError(AppError):
    """Raised when an operation violates a uniqueness constraint."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
        )


class ValidationError(AppError):
    """Raised when input fails business-logic validation (beyond Pydantic)."""

    def __init__(self, message: str, details: list[dict] | None = None) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )
