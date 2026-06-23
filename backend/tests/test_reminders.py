from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_global_reminder():
    resp = client.post(
        "/api/v1/reminders",
        json={"reminder_time": "09:00", "urgency_level": "moderate"}
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["task_id"] is None
    assert data["reminder_time"] == "09:00"
    assert data["urgency_level"] == "moderate"


def test_create_task_reminder():
    import uuid
    # 1. Create a category
    cat_resp = client.post("/api/v1/categories", json={"name": f"Reminder Cat {uuid.uuid4().hex[:6]}", "color": "#000000"})
    cat_id = cat_resp.json()["data"]["id"]

    # 2. Create a task
    task_resp = client.post("/api/v1/tasks", json={
        "title": "Reminder Task",
        "category_id": cat_id,
        "recurrence": "daily",
        "evidence_mode": "text"
    })
    task_id = task_resp.json()["data"]["id"]

    # 3. Create reminder linked to task
    resp = client.post(
        "/api/v1/reminders",
        json={"task_id": task_id, "reminder_time": "14:30", "urgency_level": "urgent"}
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["task_id"] == task_id


def test_invalid_time_format():
    resp = client.post(
        "/api/v1/reminders",
        json={"reminder_time": "25:00", "urgency_level": "moderate"}
    )
    assert resp.status_code == 422


def test_update_reminder():
    resp = client.post(
        "/api/v1/reminders",
        json={"reminder_time": "10:00", "urgency_level": "gentle"}
    )
    reminder_id = resp.json()["data"]["id"]

    update_resp = client.patch(
        f"/api/v1/reminders/{reminder_id}",
        json={"reminder_time": "11:00", "is_active": False}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["reminder_time"] == "11:00"
    assert update_resp.json()["data"]["is_active"] is False


def test_delete_reminder():
    resp = client.post(
        "/api/v1/reminders",
        json={"reminder_time": "12:00", "urgency_level": "gentle"}
    )
    reminder_id = resp.json()["data"]["id"]

    del_resp = client.delete(f"/api/v1/reminders/{reminder_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/reminders/{reminder_id}")
    assert get_resp.status_code == 404
