"""
Health check endpoint.

Called by the Tauri frontend on startup to verify the backend is ready.
Also used during development to confirm DB connectivity.

This is the first endpoint to use the standard response envelope:
  ``{"success": true, "data": {...}}``
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from app.config import settings
from app.database import check_db_connection
from app.schemas.responses import HealthData, SuccessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=SuccessResponse[HealthData])
def health_check() -> dict:
    """
    Backend readiness probe.

    Returns the standard success envelope with health data including
    database connectivity status and key configuration values.
    """
    db_ok = check_db_connection()

    return {
        "success": True,
        "data": {
            "status": "healthy" if db_ok else "degraded",
            "app": settings.app_name,
            "version": settings.api_version,
            "database": "connected" if db_ok else "disconnected",
            "db_path": str(settings.db_path),
            "evidence_dir": str(settings.evidence_dir),
            "max_evidence_file_size_mb": settings.max_evidence_file_size_mb,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }
