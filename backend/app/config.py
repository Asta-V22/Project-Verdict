"""
Application configuration.

Settings are loaded in this priority order (highest wins):
  1. Environment variables
  2. ``.env`` file (if present, via pydantic-settings)
  3. Defaults defined below

All paths are computed from the OS-appropriate app data directory
(e.g. ``%LOCALAPPDATA%/Project Verdict`` on Windows).
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import platformdirs
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings with sensible defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Identity ──────────────────────────────────────────────────────
    app_name: str = "Project Verdict"
    api_version: str = "v1"
    api_prefix: str = "/api/v1"

    # ── Server ────────────────────────────────────────────────────────
    host: str = "127.0.0.1"
    port: int = 8787
    debug: bool = False

    # ── Database ──────────────────────────────────────────────────────
    db_filename: str = "verdict.db"

    # ── Evidence ──────────────────────────────────────────────────────
    max_evidence_file_size_mb: int = 10

    # ── Application Logic ─────────────────────────────────────────────
    max_backfill_days: int = 30

    # ── Logging ───────────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── CORS ──────────────────────────────────────────────────────────
    # Used when debug=False.  When debug=True, origins fall back to ["*"].
    cors_origins: list[str] = [
        "http://localhost:1420",     # Tauri dev server
        "http://localhost:5173",     # Vite dev server
        "http://127.0.0.1:1420",
        "http://127.0.0.1:5173",
        "tauri://localhost",         # Tauri v2 production (Linux/macOS)
        "https://tauri.localhost",   # Tauri v2 production (Windows)
    ]

    # ── Computed Paths ────────────────────────────────────────────────

    @property
    def app_data_dir(self) -> Path:
        """OS-appropriate persistent data directory."""
        path = Path(platformdirs.user_data_dir(self.app_name, appauthor=False))
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def db_dir(self) -> Path:
        d = self.app_data_dir / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def db_path(self) -> Path:
        return self.db_dir / self.db_filename

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    @property
    def evidence_dir(self) -> Path:
        d = self.app_data_dir / "evidence"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def log_dir(self) -> Path:
        d = self.app_data_dir / "logs"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def max_evidence_file_size_bytes(self) -> int:
        return self.max_evidence_file_size_mb * 1024 * 1024


# ── Singleton ──────────────────────────────────────────────────────────
settings = Settings()


def configure_logging() -> None:
    """
    Set up console + rotating file logging.

    Called once during application startup.  Guards against duplicate
    handler registration on hot-reload.
    """
    root = logging.getLogger()

    # Prevent duplicate handlers when uvicorn reloads
    if root.handlers:
        return

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler — always active
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    # Rotating file handler — 5 MB per file, 3 backups
    try:
        log_file = settings.log_dir / "verdict.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except Exception as exc:
        root.warning("Could not set up file logging: %s", exc)
