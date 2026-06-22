# Roadmap

## Phase 1 — MVP Accountability Loop

The goal: a fully usable desktop app where the user declares tasks,
receives reminders, submits evidence, and reviews daily performance.

### Sub-Phase 1A — Foundation ✅
- [x] SQLite database with 8 domain tables
- [x] SQLAlchemy ORM models
- [x] Alembic migrations
- [x] FastAPI backend with health endpoint
- [x] Repository layer (generic CRUD)
- [x] Notification service abstraction
- [x] Foundation hardening (error handling, testing, docs)

### Sub-Phase 1B — Task Management (next)
- [ ] Category CRUD (create, read, update, archive)
- [ ] Task CRUD (create, read, update, archive)
- [ ] Recurrence configuration
- [ ] Pydantic schemas for validation
- [ ] Integration tests

### Sub-Phase 1C — Daily Instance Engine
- [ ] Instance generation service (idempotent)
- [ ] Dashboard API endpoint
- [ ] Auto-generate instances on startup
- [ ] Task metrics updates

### Sub-Phase 1D — Evidence Submission
- [ ] File upload API (multipart)
- [ ] File storage with path safety
- [ ] Evidence CRUD
- [ ] Instance status transitions (pending -> submitted)
- [ ] Evidence file cleanup (delete file, preserve metadata)

### Sub-Phase 1E — Reminders + Polish
- [ ] APScheduler integration
- [ ] Reminder CRUD
- [ ] Desktop notifications (windows-toasts)
- [ ] Escalating urgency logic

### Sub-Phase 1F — Frontend (Tauri + React)
- [ ] Tauri v2 project setup
- [ ] React + TypeScript + Vite
- [ ] Design system (CSS tokens, components)
- [ ] Daily dashboard view
- [ ] Task management UI
- [ ] Evidence submission UI
- [ ] Reminder configuration UI

---

## Phase 2 — Intelligence (future)

- [ ] AI verification of evidence (Ollama)
- [ ] AI-generated daily verdicts (prosecutor reports)
- [ ] Behavioral pattern analysis
- [ ] Accountability debt mechanics

## Phase 3 — Integrations (future)

- [ ] Leetcode activity verification
- [ ] Git commit tracking
- [ ] VS Code activity tracking
- [ ] Browser activity analysis

## Phase 4 — Expansion (future)

- [ ] Desktop mascot
- [ ] Mobile companion app
- [ ] Gamification / reputation scoring
- [ ] Cloud sync (optional)
