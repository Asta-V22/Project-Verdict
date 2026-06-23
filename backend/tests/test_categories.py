"""
Integration tests for Category CRUD endpoints.

Covers:
  - Create with validation
  - Duplicate name conflict
  - List active (excludes archived)
  - Get by ID (found and not found)
  - Update (partial, name uniqueness)
  - Soft delete (archive)
"""

from __future__ import annotations

# ── Helpers ───────────────────────────────────────────────────────────

def _create_category(client, name="Leetcode", color="#FF5733", icon=None) -> dict:
    """Create a category and return the response data."""
    body = {"name": name, "color": color}
    if icon is not None:
        body["icon"] = icon
    resp = client.post("/api/v1/categories", json=body)
    assert resp.status_code == 201
    return resp.json()["data"]


# ── Create ────────────────────────────────────────────────────────────

class TestCreateCategory:
    """POST /api/v1/categories"""

    def test_create_success(self, client):
        resp = client.post("/api/v1/categories", json={
            "name": "Leetcode",
            "color": "#FF5733",
            "icon": "code",
        })
        assert resp.status_code == 201

        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["name"] == "Leetcode"
        assert data["color"] == "#FF5733"
        assert data["icon"] == "code"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_without_icon(self, client):
        data = _create_category(client, name="AI/ML", color="#3498DB")
        assert data["icon"] is None

    def test_create_duplicate_name(self, client):
        _create_category(client, name="Projects")
        resp = client.post("/api/v1/categories", json={
            "name": "Projects",
            "color": "#00FF00",
        })
        assert resp.status_code == 409
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "CONFLICT"

    def test_create_empty_name(self, client):
        resp = client.post("/api/v1/categories", json={
            "name": "   ",
            "color": "#FF5733",
        })
        assert resp.status_code == 422

    def test_create_invalid_color(self, client):
        resp = client.post("/api/v1/categories", json={
            "name": "Test",
            "color": "red",
        })
        assert resp.status_code == 422

    def test_create_color_normalized_to_uppercase(self, client):
        data = _create_category(client, name="Style", color="#aabbcc")
        assert data["color"] == "#AABBCC"


# ── List ──────────────────────────────────────────────────────────────

class TestListCategories:
    """GET /api/v1/categories"""

    def test_list_empty(self, client):
        resp = client.get("/api/v1/categories")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"] == []

    def test_list_returns_active_only(self, client):
        _create_category(client, name="Active", color="#111111")
        cat2 = _create_category(client, name="ToArchive", color="#222222")

        # Archive one
        client.delete(f"/api/v1/categories/{cat2['id']}")

        resp = client.get("/api/v1/categories")
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Active"


# ── Get by ID ─────────────────────────────────────────────────────────

class TestGetCategory:
    """GET /api/v1/categories/{id}"""

    def test_get_existing(self, client):
        created = _create_category(client, name="DSA", color="#ABCDEF")
        resp = client.get(f"/api/v1/categories/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "DSA"

    def test_get_not_found(self, client):
        resp = client.get("/api/v1/categories/nonexistent-id")
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"


# ── Update ────────────────────────────────────────────────────────────

class TestUpdateCategory:
    """PATCH /api/v1/categories/{id}"""

    def test_update_name(self, client):
        created = _create_category(client, name="Old Name", color="#111111")
        resp = client.patch(
            f"/api/v1/categories/{created['id']}",
            json={"name": "New Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "New Name"
        # Color should be unchanged
        assert resp.json()["data"]["color"] == "#111111"

    def test_update_color_only(self, client):
        created = _create_category(client, name="ColorTest", color="#111111")
        resp = client.patch(
            f"/api/v1/categories/{created['id']}",
            json={"color": "#999999"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["color"] == "#999999"
        assert resp.json()["data"]["name"] == "ColorTest"

    def test_update_duplicate_name(self, client):
        _create_category(client, name="Taken", color="#111111")
        other = _create_category(client, name="Other", color="#222222")

        resp = client.patch(
            f"/api/v1/categories/{other['id']}",
            json={"name": "Taken"},
        )
        assert resp.status_code == 409

    def test_update_not_found(self, client):
        resp = client.patch(
            "/api/v1/categories/nonexistent-id",
            json={"name": "Nope"},
        )
        assert resp.status_code == 404


# ── Delete (archive) ──────────────────────────────────────────────────

class TestDeleteCategory:
    """DELETE /api/v1/categories/{id}"""

    def test_archive(self, client):
        created = _create_category(client, name="ToDelete", color="#111111")
        resp = client.delete(f"/api/v1/categories/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False

    def test_archived_not_in_active_list(self, client):
        created = _create_category(client, name="Archived", color="#111111")
        client.delete(f"/api/v1/categories/{created['id']}")

        resp = client.get("/api/v1/categories")
        names = [c["name"] for c in resp.json()["data"]]
        assert "Archived" not in names

    def test_archived_still_accessible_by_id(self, client):
        created = _create_category(client, name="StillThere", color="#111111")
        client.delete(f"/api/v1/categories/{created['id']}")

        resp = client.get(f"/api/v1/categories/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False

    def test_delete_not_found(self, client):
        resp = client.delete("/api/v1/categories/nonexistent-id")
        assert resp.status_code == 404
