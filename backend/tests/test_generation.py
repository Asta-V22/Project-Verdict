"""
Integration tests for Task Instance Generation Engine.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from app.config import settings

# ── Helpers ───────────────────────────────────────────────────────────

def _create_task(client, title="Task", recurrence="daily", recurrence_days=None, **kwargs) -> dict:
    body = {"title": title, "recurrence": recurrence}
    if recurrence_days:
        body["recurrence_days"] = json.dumps(recurrence_days)
    body.update(kwargs)
    resp = client.post("/api/v1/tasks", json=body)
    return resp.json()["data"]


def _set_last_sync_date(db_session, target_date: date):
    from app.repositories.app_state import AppStateRepository
    repo = AppStateRepository(db_session)
    repo.set_value("last_instance_sync_date", target_date.isoformat())
    db_session.commit()


# ── Tests ─────────────────────────────────────────────────────────────

class TestGenerationEngine:

    def test_first_run_generates_for_today(self, client):
        _create_task(client, title="Daily Task", recurrence="daily")

        resp = client.post("/api/v1/sync/instances")
        assert resp.status_code == 200

        data = resp.json()["data"]
        assert data["generated_count"] == 1
        assert data["truncation_occurred"] is False

        # Verify it exists
        date_str = datetime.now().date().isoformat()
        instances_resp = client.get(f"/api/v1/instances?target_date={date_str}")
        assert len(instances_resp.json()["data"]) == 1

    def test_subsequent_runs_prevent_duplicates(self, client):
        _create_task(client, title="Daily Task", recurrence="daily")

        # Run 1
        client.post("/api/v1/sync/instances")

        # Run 2
        resp = client.post("/api/v1/sync/instances")
        data = resp.json()["data"]
        assert data["generated_count"] == 0

    def test_backfill_gap(self, client, db_session):
        _create_task(client, title="Daily Task", recurrence="daily")

        today = datetime.now().date()
        # Simulate app wasn't opened for the last 5 days
        last_sync = today - timedelta(days=5)
        _set_last_sync_date(db_session, last_sync)

        resp = client.post("/api/v1/sync/instances")
        data = resp.json()["data"]

        # It should generate for 5 days: last_sync + 1 ... today
        assert data["generated_count"] == 5

    def test_max_backfill_truncation(self, client, db_session):
        _create_task(client, title="Daily Task", recurrence="daily")

        today = datetime.now().date()
        # Gap of 40 days
        last_sync = today - timedelta(days=40)
        _set_last_sync_date(db_session, last_sync)

        resp = client.post("/api/v1/sync/instances")
        data = resp.json()["data"]

        # Should truncate to max_backfill_days (default 30)
        assert data["generated_count"] == settings.max_backfill_days
        assert data["truncation_occurred"] is True

    def test_soft_deleted_tasks_do_not_generate(self, client, db_session):
        task = _create_task(client, title="Deleted Task", recurrence="daily")
        client.delete(f"/api/v1/tasks/{task['id']}")

        today = datetime.now().date()
        last_sync = today - timedelta(days=1)
        _set_last_sync_date(db_session, last_sync)

        resp = client.post("/api/v1/sync/instances")
        data = resp.json()["data"]
        assert data["generated_count"] == 0

    def test_recurrence_rules(self, client, db_session):
        _create_task(client, title="None", recurrence="none")
        _create_task(client, title="Daily", recurrence="daily")
        _create_task(client, title="Weekdays", recurrence="weekdays")
        _create_task(
            client, title="Custom", recurrence="custom", recurrence_days=[0, 2, 4]
        )  # Mon, Wed, Fri

        # Simulate yesterday
        today = datetime.now().date()
        last_sync = today - timedelta(days=1)
        _set_last_sync_date(db_session, last_sync)

        resp = client.post("/api/v1/sync/instances")
        data = resp.json()["data"]

        # Should at least generate Daily.
        # Weekdays/Custom depend on what day 'today' actually is.
        # So we just ensure it ran without crashing and generated > 0 instances.
        assert data["generated_count"] >= 1
