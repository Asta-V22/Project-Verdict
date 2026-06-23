# Phase 1C: Task Instance Generation Engine Summary

This document summarizes the changes and features implemented during Sub-Phase 1C, focusing on the engine that converts `Task` templates into daily `TaskInstance` obligations.

## 1. Engine Design and Data Flow
The generation engine was implemented using a **Client-Driven Sync** model, avoiding the need for constantly running background cron jobs.
- **Endpoint**: `POST /api/v1/sync/instances`
- The endpoint accepts no request body. The server natively determines the target date (today's date).
- The engine iterates over all active tasks, evaluates their recurrence rules (`Daily`, `Weekdays`, `Custom`), and creates `TaskInstance` records for dates that require them.
- `due_time` is snapshotted from the parent `Task` onto the `TaskInstance` at creation, ensuring future modifications to the parent task do not alter historical data.

## 2. AppState Tracking
A new `AppStateRepository` was implemented on top of the existing `AppState` model.
- It acts as a lightweight JSON key-value store for global settings.
- It tracks the `last_instance_sync_date` so the engine knows exactly which days to evaluate during backfill. This prevents redundant scans of the entire database.

## 3. Backfill Truncation & Configuration
- Added `max_backfill_days` configuration to `app/config.py` (defaults to 30 days).
- If the user hasn't synced in a long time (e.g., 40 days), the engine limits the backfill to the most recent 30 days to prevent overwhelming the database and UI.
- The sync API returns a response payload including a boolean flag indicating if truncation occurred:
  ```json
  {
    "success": true,
    "data": {
      "generated_count": 30,
      "synced_up_to": "2026-06-23",
      "truncation_occurred": true
    }
  }
  ```

## 4. Edge Case Protections
- **Duplicates**: The engine queries existing instances for the target date range and stores them in an in-memory lookup set before generation. This safely bypasses `IntegrityError` collisions from the database `UNIQUE(task_id, instance_date)` constraint.
- **Soft Deletions**: The `TaskRepository.get_active()` method is used, strictly isolating the engine from generating instances for deleted tasks.
- **Malformed Custom Recurrence**: JSON decoding errors on the `recurrence_days` array are handled safely, skipping generation rather than crashing the loop.

## 5. Endpoints Created

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/sync/instances` | Trigger the sync engine up to today |
| `GET` | `/api/v1/instances?target_date=...` | Fetch instances for the daily dashboard |
| `GET` | `/api/v1/instances/{id}` | Get a single instance by ID |
| `PATCH` | `/api/v1/instances/{id}/status` | Update instance status (e.g., pending -> skipped) |

## 6. Files Created
- `app/repositories/app_state.py`
- `app/schemas/task_instance.py`
- `app/repositories/task_instance.py`
- `app/services/task_instance_service.py`
- `app/services/generation_service.py`
- `app/routers/instances.py`
- `tests/test_generation.py`

## 7. Files Modified
- `app/config.py` — Added `max_backfill_days`.
- `app/routers/__init__.py` — Exported `instances_router`.
- `app/main.py` — Mounted `instances_router`.

## 8. Verification Results
- **Testing**: Created a robust test suite (`test_generation.py`) that successfully mocks `AppState` sync dates to simulate 5-day gaps, 40-day gaps, soft-deleted tasks, and recurrence types. All passed (`100% Passed`).
- **Code Quality**: The `ruff check .` linter runs completely clean on the entire backend.
