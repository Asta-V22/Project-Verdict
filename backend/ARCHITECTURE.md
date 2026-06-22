# Architecture

## System Overview

Project Verdict is a local-first, single-user desktop application built as a
**Tauri shell** wrapping a **React + TypeScript** frontend that talks to a
**Python FastAPI** backend over HTTP on `localhost:8787`.

```
┌──────────────────────────────────────────────┐
│          Tauri (Rust) Desktop Shell           │
│  ┌────────────────────────────────────────┐  │
│  │      React + TypeScript (WebView)      │  │
│  │           fetch() / TanStack Query     │  │
│  └──────────────┬─────────────────────────┘  │
│                 │ HTTP REST                   │
│  ┌──────────────▼─────────────────────────┐  │
│  │      Python FastAPI Sidecar            │  │
│  │      localhost:8787                    │  │
│  └──────────────┬─────────────────────────┘  │
│                 │ SQLAlchemy                  │
│  ┌──────────────▼─────────────────────────┐  │
│  │        SQLite Database                 │  │
│  │   %LOCALAPPDATA%/Project Verdict/      │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

## Backend Layers

```
Router  →  Service  →  Repository  →  SQLAlchemy  →  SQLite
  ▲           ▲            ▲
  │           │            │
Schemas    Exceptions    Models
```

| Layer | Responsibility | Location |
|---|---|---|
| **Routers** | Parse HTTP, call services, return responses | `app/routers/` |
| **Services** | Business logic, validation, orchestration | `app/services/` |
| **Repositories** | Data access, queries, CRUD operations | `app/repositories/` |
| **Models** | SQLAlchemy ORM table definitions | `app/models/` |
| **Schemas** | Pydantic request/response validation | `app/schemas/` |
| **Exceptions** | Custom error hierarchy | `app/exceptions.py` |
| **Middleware** | Cross-cutting concerns (logging) | `app/middleware.py` |
| **Config** | Settings, paths, environment loading | `app/config.py` |
| **Database** | Engine, session factory, initialization | `app/database.py` |
| **Dependencies** | FastAPI `Depends()` providers | `app/dependencies.py` |

## Data Flow (Request Lifecycle)

1. **Request arrives** at FastAPI via HTTP
2. **RequestLoggingMiddleware** starts a timer
3. **Router** validates input via Pydantic schemas
4. **Router** calls the appropriate service
5. **Service** applies business logic, calls repository
6. **Repository** executes SQLAlchemy queries
7. **Service** returns result to router
8. **Router** wraps result in `SuccessResponse` envelope
9. **Middleware** logs method, path, status, duration
10. **Response** sent to frontend

On error, **global exception handlers** catch exceptions at any layer and
return the standard `ErrorResponse` envelope.

## Database Schema

8 domain tables plus `alembic_version`:

| Table | Purpose |
|---|---|
| `categories` | User-defined task labels |
| `tasks` | Master task definitions |
| `task_instances` | One row per task per day |
| `evidence` | Proof of completion |
| `reminders` | Configurable notification rules |
| `task_metrics` | Pre-computed streaks and debt |
| `daily_verdicts` | Daily completion summaries |
| `app_state` | Key-value settings store |

## Key Design Decisions

1. **Sidecar pattern** — Python runs as a separate process spawned by Tauri.
   Communication is plain HTTP REST on localhost.

2. **Evidence on instances, not tasks** — Completion belongs to the daily
   instance, not the master task. This enables per-day tracking.

3. **Soft delete everywhere** — Tasks and categories are archived, never
   destroyed. Historical data is always preserved.

4. **Pre-computed metrics** — `task_metrics` avoids expensive recalculation
   from historical data. Updated incrementally.

5. **Standard response envelope** — Every endpoint returns
   `{"success": bool, "data": ...}` or `{"success": bool, "error": {...}}`.

## File Storage

```
%LOCALAPPDATA%/Project Verdict/
├── data/verdict.db        # SQLite database
├── evidence/              # Uploaded proof files
│   └── 2026-06-22/        # Organized by date
│       └── {instance_id}/ # Then by instance
└── logs/verdict.log       # Rotating application log
```
