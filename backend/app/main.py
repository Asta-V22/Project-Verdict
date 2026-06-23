"""
Project Verdict -- FastAPI application entry point.

Configures:
  - Global exception handlers  (consistent JSON error envelope)
  - CORS middleware             (localhost-restricted, or ``*`` in debug)
  - Request logging middleware  (method, path, status, duration)
  - Lifespan handler            (DB init, sidecar readiness signal)
  - Router registration
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import configure_logging, settings
from app.core.scheduler import start_scheduler, stop_scheduler
from app.database import init_db
from app.exceptions import AppError
from app.middleware import RequestLoggingMiddleware
from app.routers import (
    categories_router,
    evidence_router,
    health_router,
    instances_router,
    reminders_router,
    tasks_router,
)

logger = logging.getLogger(__name__)


# ── Exception Handlers ────────────────────────────────────────────────

def _register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers that produce the standard error envelope."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Wrap FastAPI's built-in HTTP errors (404, 405, etc.) in our envelope."""
        code_map = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": code_map.get(exc.status_code, "HTTP_ERROR"),
                    "message": str(exc.detail),
                    "details": [],
                },
            },
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Handle our custom exception hierarchy."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Reformat Pydantic validation errors into our standard envelope."""
        details = []
        for err in exc.errors():
            field = " -> ".join(str(loc) for loc in err.get("loc", []))
            details.append({"field": field, "message": err.get("msg", "")})
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": details,
                },
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        """Convert SQLAlchemy constraint violations to 409 Conflict."""
        logger.warning("Database integrity error: %s", exc.orig)
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": {
                    "code": "CONFLICT",
                    "message": "A record with this value already exists",
                    "details": [],
                },
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all for unhandled exceptions.  Hides details unless debug=True."""
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        message = str(exc) if settings.debug else "An unexpected error occurred"
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": message,
                    "details": [],
                },
            },
        )


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""

    # ── Startup ───────────────────────────────────────────────────────
    configure_logging()
    logger.info("=" * 60)
    logger.info("  %s v%s starting up", settings.app_name, settings.api_version)
    logger.info("=" * 60)

    logger.info("Initializing database...")
    init_db()
    logger.info("Database ready at: %s", settings.db_path)
    logger.info("Evidence directory: %s", settings.evidence_dir)
    logger.info("Max evidence file size: %d MB", settings.max_evidence_file_size_mb)
    logger.info("Debug mode: %s", settings.debug)
    logger.info(
        "API available at: http://%s:%d%s",
        settings.host,
        settings.port,
        settings.api_prefix,
    )

    # Signal readiness to Tauri sidecar manager
    print("ready", flush=True)

    start_scheduler()

    yield

    # ── Shutdown ──────────────────────────────────────────────────────
    logger.info("Shutting down %s...", settings.app_name)
    stop_scheduler()


# ── App Factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.app_name,
        description="Evidence-driven accountability system",
        version=settings.api_version,
        lifespan=lifespan,
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )

    # Exception handlers
    _register_exception_handlers(app)

    # CORS — permissive in debug, restricted to localhost otherwise
    origins = ["*"] if settings.debug else settings.cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Routers
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(categories_router, prefix=settings.api_prefix)
    app.include_router(tasks_router, prefix=settings.api_prefix)
    app.include_router(instances_router, prefix=settings.api_prefix)
    app.include_router(evidence_router, prefix=settings.api_prefix)
    app.include_router(reminders_router, prefix=settings.api_prefix)

    return app


# ── Application instance ──────────────────────────────────────────────
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
    )
