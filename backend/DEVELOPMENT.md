# Development Guide

## Prerequisites

- Python 3.11+
- Git

## Initial Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies (includes dev tools)
pip install -r requirements-dev.txt

# Copy environment config (optional — defaults work fine)
copy .env.example .env
```

## Running the Server

```bash
# Development (with auto-reload)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8787 --reload

# Or simply
python -m app.main
```

The server starts at `http://127.0.0.1:8787`.

- **API docs**: http://127.0.0.1:8787/api/v1/docs
- **Health check**: http://127.0.0.1:8787/api/v1/health

## Database

The SQLite database is stored at:
```
%LOCALAPPDATA%/Project Verdict/data/verdict.db
```

### Migrations

```bash
# Apply pending migrations
python -m alembic upgrade head

# Generate a new migration after model changes
python -m alembic revision --autogenerate -m "description_of_change"

# View migration history
python -m alembic history
```

## Testing

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run a specific test file
python -m pytest tests/test_health.py

# Run a specific test class or method
python -m pytest tests/test_health.py::TestHealthEndpoint::test_reports_healthy_status
```

Tests use an **in-memory SQLite database** — they never touch the production
database. Each test gets a clean transactional session that rolls back
automatically.

## Linting & Formatting

```bash
# Check for lint errors
python -m ruff check .

# Auto-fix lint errors
python -m ruff check . --fix

# Format code
python -m ruff format .

# Type checking (informational, not enforced)
python -m mypy app/
```

## Project Conventions

### Code Style
- Line length: 100 characters
- Imports: sorted by `isort` (via ruff)
- Quotes: double quotes
- Type hints: used on function signatures, not enforced by mypy strictly

### Architecture Rules
- **Routers** handle HTTP only — no business logic
- **Services** contain business logic — no HTTP awareness
- **Repositories** handle data access — no business logic
- **Models** are plain ORM definitions — no methods beyond `__repr__`
- **Schemas** validate input/output — separate from ORM models

### Naming
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Database tables: `snake_case` (plural)
- API URLs: `kebab-case` (plural nouns)

### Error Handling
- Use `raise NotFoundError("Task", task_id)` — never construct raw HTTP responses in services
- Global exception handlers convert exceptions to the standard error envelope
- Never catch exceptions silently unless you have a specific recovery strategy

### Response Format
- Always return the standard envelope: `{"success": true/false, ...}`
- Use `response_model=SuccessResponse[T]` on endpoints for OpenAPI docs
- See `API_CONTRACT.md` for the full specification

## Environment Variables

See `.env.example` for all configurable values. All have sensible defaults.
The `.env` file is optional.

## Logs

Application logs are written to:
- Console (always)
- `%LOCALAPPDATA%/Project Verdict/logs/verdict.log` (rotating, 5 MB, 3 backups)
