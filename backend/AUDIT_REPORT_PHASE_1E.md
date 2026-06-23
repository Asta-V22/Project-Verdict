# Backend Architecture Audit Report (Pre-Phase 1E)

## Executive Summary
A comprehensive audit of Sub-Phases 1A through 1D reveals a robust, well-structured FastAPI backend that adheres closely to the requested Service/Repository architecture. The schema designs for `Task`, `TaskInstance`, and `Evidence` accurately capture the accountability workflows. Security measures against path traversal and oversized payloads are well implemented. 

However, before proceeding to Sub-Phase 1E (Reminders & APScheduler integration), several critical gaps were identified—specifically around dead code in the repository layer, missing validations for archived tasks, and a missing file-serving endpoint which would block frontend evidence viewers.

---

## 1. Critical Issues (Must Fix Before 1E)

### 1.1 Dead Code / Broken Repository Abstraction
**Finding:** `EvidenceRepository` exists and is instantiated in `EvidenceService.__init__`, but it is never actually used.
**Detail:** In `EvidenceService.submit_file_evidence()`, the code directly executes `self.db.add(evidence)` instead of routing through the repository layer.
**Fix:** Refactor `EvidenceService` to use `self.repo.create()` or similar repository methods to maintain strict architectural boundaries.

### 1.2 Missing Validation on Archived Entities
**Finding:** Evidence can currently be submitted to instances of archived (soft-deleted) tasks.
**Detail:** The prompt required verifying that "Archived/inactive entities cannot receive new evidence." Currently, `EvidenceService` validates that the `TaskInstance` exists, but it fails to verify `instance.task.is_active`. If a user archives a task, its pending instances from today will still illegally accept evidence.
**Fix:** Add `if not instance.task.is_active: raise ValidationError(...)` in the submission flow.

### 1.3 Missing GET Evidence Endpoints
**Finding:** No endpoint exists to serve the actual physical evidence files back to the frontend.
**Detail:** While the metadata is serialized within `TaskInstanceResponse`, there is no `GET /api/v1/evidence/{id}/file` endpoint or `StaticFiles` mount to actually stream the `image/png` or `application/pdf` bytes back to the UI. The frontend "Evidence Viewer" deliverable is completely blocked by this.
**Fix:** Implement a dedicated endpoint to securely stream evidence files from the `LocalStorageProvider`.

---

## 2. Recommended Improvements

### 2.1 Decoupling UUID generation
Currently, `uuid.uuid4().hex` is generated inside the `EvidenceService` just prior to calling `self.storage.save_file()`. While functional, the `StorageProvider` abstraction might be better served by handling the UUID generation itself and returning the finalized disk path to the service. This ensures the storage layer has complete sovereignty over disk filenames.

---

## 3. Technical Debt Items

### 3.1 Unused Local Variables in Tests
Minor tech debt: `test_evidence.py` contains some commented-out logic regarding file sizes and mock assertions. These should be cleaned up to maintain a pristine test suite.

---

## 4. Security Findings

**Status: PASS**
- **Idempotency:** `EvidenceService` correctly transitions `PENDING` -> `SUBMITTED`. If the status is already `SUBMITTED`, it safely appends the evidence without throwing an error.
- **Rollbacks:** The `test_rollback_on_db_error` test confirms that if `self.db.commit()` raises an IntegrityError or DB disconnect, `self.storage.delete_file()` is explicitly called, preventing orphaned files.
- **404s:** Uploading evidence to a non-existent instance ID correctly yields a `404 Not Found`.

---

## 5. APScheduler Readiness Assessment

The current stack is SQLite-based with `check_same_thread=False` and WAL mode enabled.
- **Database Safety:** SQLite in WAL mode is thread-safe for reads, but concurrent writes will queue. The `busy_timeout = 5000` configuration provides a 5-second buffer. This is safe for a lightweight APScheduler running in the background.
- **Session Management:** FastAPI's `Depends(get_db)` cannot be used in a background APScheduler thread. Future cron jobs will need to explicitly instantiate `SessionLocal()` in a context manager.
- **Readiness:** The backend architecture is ready to support background jobs, provided the scheduler creates isolated database sessions.

---

## 6. Go / No-Go Recommendation

**Recommendation: NO-GO for Sub-Phase 1E.**

**Action Required:** Sub-Phase 1E (Reminders & Polish) should be paused until a minor **Phase 1D.1 (Audit Fixes)** patch is executed.

The missing evidence GET endpoint and the missing validation on archived tasks represent functional blockers that violate the core project constraints. I strongly recommend authorizing a quick refactor pass to address Sections 1.1, 1.2, and 1.3 before advancing the roadmap.
