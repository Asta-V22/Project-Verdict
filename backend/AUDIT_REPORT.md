# Pre-Phase 1D Architectural Audit Report

This report evaluates the current codebase against the requirements for Sub-Phase 1D (Evidence System), analyzing schema readiness, security constraints, and transaction boundaries.

## 1. Schema & Model Readiness
The data models (`TaskInstance` and `Evidence`) are structurally sound and ready for Phase 1D.
- The `Evidence` table correctly links to `TaskInstance` via `instance_id`.
- Support for `text`, `link`, `screenshot`, and `file` evidence types is already defined.
- `TaskInstance` includes `status` and `completed_at` to accurately track submission workflows.

## 2. Indexes, Constraints, and Foreign Keys
- `TaskInstance.task_id` and `Evidence.instance_id` are both properly indexed.
- `Evidence` uses `cascade="all, delete-orphan"` ensuring database referential integrity.
- `app/database.py` enforces `PRAGMA foreign_keys = ON` upon every SQLite connection, preventing silent orphaned records.

## 3. Repository/Service Abstractions
- The `BaseRepository` pattern relies strictly on SQLAlchemy Sessions. This makes it trivial to perform multi-table atomic transactions (e.g., creating an `Evidence` row while simultaneously updating the `TaskInstance` status) within the same `Session`. 

## 4. API Contracts
- No existing endpoints will break. Phase 1D will purely introduce new endpoints (e.g., `POST /api/v1/instances/{id}/evidence`) using `multipart/form-data` without mutating the existing JSON response structures.

## 5. Security Concerns
- `app/utils/file_safety.py` was introduced in the Foundation phase and handles:
  - Filename sanitization (stripping dangerous OS characters and null bytes).
  - Path traversal protection (verifying the absolute path does not escape the configured `evidence_dir`).
  - Configurable file-size validation.

## 6. Transaction Boundary Issues

### Must Fix Before Phase 1D
None. The foundations are solid.

### Should Fix Soon (During Phase 1D Implementation)
- **Orphaned File Risk on Rollback**: When submitting evidence, the physical file must be written to disk before the database transaction commits. The `EvidenceService` must be designed with an exception block: if `db.commit()` fails due to an integrity error or validation issue, the newly written physical file must be immediately deleted (`os.remove()`) to prevent filesystem bloat.
- **Orphaned File Risk on Delete**: If an instance is ever hard-deleted (despite soft-delete policies), the SQLAlchemy `cascade` will drop the `Evidence` row but will *not* delete the physical file. The application should handle file deletion at the service layer before issuing delete commands.

### Can Safely Defer
- **Background Cleanup Worker**: A worker to occasionally sweep the `evidence_dir` for files that do not have a matching database row. This can be deferred to a much later phase.

## 7. Technical Debt
The codebase is 100% clean, fully typed, heavily tested, and `ruff` compliant. There is no technical debt hindering the next phase.

---

**Conclusion**
Phase 1D can proceed without architectural changes.
