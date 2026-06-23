"""
Integration tests for Task CRUD endpoints.

Covers:
  - Create with validation (including category existence)
  - List active (excludes archived)
  - Get by ID (found and not found)
  - Update (partial updates, invalid category update)
  - Soft delete (archive)
"""

from __future__ import annotations

# ── Helpers ───────────────────────────────────────────────────────────

def _create_category(client, name="Coding") -> dict:
    """Create a test category and return its data."""
    resp = client.post("/api/v1/categories", json={"name": name, "color": "#000000"})
    assert resp.status_code == 201
    return resp.json()["data"]


def _create_task(client, title="Do Leetcode", category_id=None, **kwargs) -> dict:
    """Create a task and return the response data."""
    body = {"title": title}
    if category_id:
        body["category_id"] = category_id
    body.update(kwargs)

    resp = client.post("/api/v1/tasks", json=body)
    assert resp.status_code == 201
    return resp.json()["data"]


# ── Create ────────────────────────────────────────────────────────────

class TestCreateTask:
    """POST /api/v1/tasks"""

    def test_create_success(self, client):
        resp = client.post("/api/v1/tasks", json={
            "title": "Daily Workout",
            "due_time": "19:00",
            "evidence_mode": "text"
        })
        assert resp.status_code == 201

        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["title"] == "Daily Workout"
        assert data["due_time"] == "19:00"
        assert data["evidence_mode"] == "text"
        assert data["is_active"] is True
        assert "id" in data

    def test_create_with_category(self, client):
        cat = _create_category(client)
        data = _create_task(client, category_id=cat["id"])
        assert data["category_id"] == cat["id"]
        # Category relationship should be joined/included
        assert data["category"]["name"] == cat["name"]

    def test_create_invalid_category(self, client):
        resp = client.post("/api/v1/tasks", json={
            "title": "Bad Task",
            "category_id": "nonexistent"
        })
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_create_empty_title(self, client):
        resp = client.post("/api/v1/tasks", json={"title": "   "})
        assert resp.status_code == 422

    def test_create_invalid_due_time(self, client):
        resp = client.post("/api/v1/tasks", json={
            "title": "Bad Time",
            "due_time": "25:00" # Invalid hour
        })
        assert resp.status_code == 422


# ── List ──────────────────────────────────────────────────────────────

class TestListTasks:
    """GET /api/v1/tasks"""

    def test_list_empty(self, client):
        resp = client.get("/api/v1/tasks")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_list_returns_active_only(self, client):
        _create_task(client, title="Active Task")
        task2 = _create_task(client, title="To Archive Task")

        # Archive one
        client.delete(f"/api/v1/tasks/{task2['id']}")

        resp = client.get("/api/v1/tasks")
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["title"] == "Active Task"


# ── Get by ID ─────────────────────────────────────────────────────────

class TestGetTask:
    """GET /api/v1/tasks/{id}"""

    def test_get_existing(self, client):
        created = _create_task(client, title="Learn Rust")
        resp = client.get(f"/api/v1/tasks/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Learn Rust"

    def test_get_not_found(self, client):
        resp = client.get("/api/v1/tasks/nonexistent-id")
        assert resp.status_code == 404


# ── Update ────────────────────────────────────────────────────────────

class TestUpdateTask:
    """PATCH /api/v1/tasks/{id}"""

    def test_update_title(self, client):
        created = _create_task(client, title="Old Title")
        resp = client.patch(
            f"/api/v1/tasks/{created['id']}",
            json={"title": "New Title"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "New Title"

    def test_update_category(self, client):
        created = _create_task(client)
        cat = _create_category(client, name="New Cat")

        resp = client.patch(
            f"/api/v1/tasks/{created['id']}",
            json={"category_id": cat["id"]},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["category_id"] == cat["id"]

    def test_update_invalid_category(self, client):
        created = _create_task(client)
        resp = client.patch(
            f"/api/v1/tasks/{created['id']}",
            json={"category_id": "nonexistent"},
        )
        assert resp.status_code == 404

    def test_update_not_found(self, client):
        resp = client.patch(
            "/api/v1/tasks/nonexistent-id",
            json={"title": "Nope"},
        )
        assert resp.status_code == 404


# ── Delete (archive) ──────────────────────────────────────────────────

class TestDeleteTask:
    """DELETE /api/v1/tasks/{id}"""

    def test_archive(self, client):
        created = _create_task(client, title="ToDelete")
        resp = client.delete(f"/api/v1/tasks/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False

    def test_archived_not_in_active_list(self, client):
        created = _create_task(client, title="Archived")
        client.delete(f"/api/v1/tasks/{created['id']}")

        resp = client.get("/api/v1/tasks")
        titles = [t["title"] for t in resp.json()["data"]]
        assert "Archived" not in titles

    def test_archived_still_accessible_by_id(self, client):
        created = _create_task(client, title="StillThere")
        client.delete(f"/api/v1/tasks/{created['id']}")

        resp = client.get(f"/api/v1/tasks/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False
