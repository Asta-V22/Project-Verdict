"""
Integration tests for Evidence Submission.
"""

from __future__ import annotations

import io
from unittest import mock

from app.config import settings


def _create_task_and_instance(client) -> str:
    """Helper to create a task, sync, and return the instance ID."""
    body = {"title": "Evidence Task", "recurrence": "daily"}
    client.post("/api/v1/tasks", json=body)
    client.post("/api/v1/sync/instances")

    # Get the instance
    import datetime
    today = datetime.datetime.now().date().isoformat()
    resp = client.get(f"/api/v1/instances?target_date={today}")
    instances = resp.json()["data"]
    # return the last generated instance id
    return instances[-1]["id"]


class TestEvidenceSubmission:

    def test_submit_valid_evidence(self, client):
        instance_id = _create_task_and_instance(client)

        # Mock file content
        file_content = b"fake image content"
        file = io.BytesIO(file_content)

        resp = client.post(
            f"/api/v1/instances/{instance_id}/evidence",
            files={"file": ("test.png", file, "image/png")},
            data={"notes": "This is proof"}
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["evidence_type"] == "file"
        assert data["file_name"] == "test.png"
        assert data["file_size"] == len(file_content)
        assert data["notes"] == "This is proof"

        # Verify instance is now SUBMITTED
        inst_resp = client.get(f"/api/v1/instances/{instance_id}")
        assert inst_resp.json()["data"]["status"] == "submitted"
        # Verify evidence is listed
        assert len(inst_resp.json()["data"]["evidence"]) == 1

    def test_invalid_mime_type(self, client):
        instance_id = _create_task_and_instance(client)

        file = io.BytesIO(b"bad script")
        resp = client.post(
            f"/api/v1/instances/{instance_id}/evidence",
            files={"file": ("test.sh", file, "application/x-sh")}
        )

        assert resp.status_code == 422
        assert "File type not allowed" in resp.json()["error"]["message"]

    def test_file_too_large(self, client):
        instance_id = _create_task_and_instance(client)

        # We don't actually need to send 11MB over the wire if we mock the size check,
        # but since we read getattr(file, 'size') or fallback to tell(), we can just mock tell

        pass  # mock size in settings directly
        # However, sending 10MB in memory test is fine, it's fast. Let's just do 10MB + 1 byte
        # Wait, that might be too slow. Let's mock the max_size in settings temporarily.

        original_limit = settings.max_evidence_file_size_mb
        settings.max_evidence_file_size_mb = 0 # 0MB means everything is too large

        try:
            file = io.BytesIO(b"small content")
            resp = client.post(
                f"/api/v1/instances/{instance_id}/evidence",
                files={"file": ("test.png", file, "image/png")}
            )
            assert resp.status_code == 422
            assert "File size must be between" in resp.json()["error"]["message"]
        finally:
            settings.max_evidence_file_size_mb = original_limit

    def test_idempotent_submissions(self, client):
        instance_id = _create_task_and_instance(client)

        file1 = io.BytesIO(b"proof 1")
        resp1 = client.post(
            f"/api/v1/instances/{instance_id}/evidence",
            files={"file": ("proof1.png", file1, "image/png")}
        )
        assert resp1.status_code == 201

        # Second submission should succeed and append evidence, not fail
        file2 = io.BytesIO(b"proof 2")
        resp2 = client.post(
            f"/api/v1/instances/{instance_id}/evidence",
            files={"file": ("proof2.png", file2, "image/png")}
        )
        assert resp2.status_code == 201

        inst_resp = client.get(f"/api/v1/instances/{instance_id}")
        data = inst_resp.json()["data"]
        assert data["status"] == "submitted"
        assert len(data["evidence"]) == 2

    @mock.patch("app.core.storage.LocalStorageProvider.delete_file")
    def test_rollback_on_db_error(self, mock_delete, client):
        """Test that if the DB commit fails, the file is deleted from disk."""
        instance_id = _create_task_and_instance(client)

        import pytest
        # We need to force a database error. We can do this by mocking the db session commit
        with mock.patch("sqlalchemy.orm.Session.commit", side_effect=Exception("DB Failure")):
            file = io.BytesIO(b"content")
            with pytest.raises(Exception, match="DB Failure"):
                client.post(
                    f"/api/v1/instances/{instance_id}/evidence",
                    files={"file": ("test.png", file, "image/png")}
                )

            # Ensure delete_file was called to cleanup the written file
            mock_delete.assert_called_once()

    def test_submission_to_archived_task_rejected(self, client):
        instance_id = _create_task_and_instance(client)

        # Archive the parent task
        inst_resp = client.get(f"/api/v1/instances/{instance_id}")
        task_id = inst_resp.json()["data"]["task_id"]
        client.delete(f"/api/v1/tasks/{task_id}")

        # Attempt submission
        file = io.BytesIO(b"content")
        resp = client.post(
            f"/api/v1/instances/{instance_id}/evidence",
            files={"file": ("test.png", file, "image/png")}
        )
        assert resp.status_code == 422
        assert "Cannot submit evidence to an archived task" in resp.json()["error"]["message"]

    def test_evidence_retrieval(self, client):
        instance_id = _create_task_and_instance(client)

        # Submit valid evidence
        file_content = b"fake image content"
        file = io.BytesIO(file_content)
        resp = client.post(
            f"/api/v1/instances/{instance_id}/evidence",
            files={"file": ("test.png", file, "image/png")}
        )
        evidence_id = resp.json()["data"]["id"]

        # Retrieve evidence file
        get_resp = client.get(f"/api/v1/evidence/{evidence_id}/file")
        assert get_resp.status_code == 200
        assert get_resp.content == file_content
        assert 'filename="test.png"' in get_resp.headers["content-disposition"]

    def test_nonexistent_evidence_retrieval(self, client):
        resp = client.get("/api/v1/evidence/does-not-exist/file")
        assert resp.status_code == 404

    @mock.patch(
        "app.core.storage.LocalStorageProvider.get_file_path",
        side_effect=FileNotFoundError
    )
    def test_missing_physical_file_retrieval(self, mock_get_path, client):
        instance_id = _create_task_and_instance(client)

        # Submit valid evidence
        file = io.BytesIO(b"content")
        resp = client.post(
            f"/api/v1/instances/{instance_id}/evidence",
            files={"file": ("test.png", file, "image/png")}
        )
        evidence_id = resp.json()["data"]["id"]

        # With get_file_path mocked to raise FileNotFoundError, it should yield 404
        get_resp = client.get(f"/api/v1/evidence/{evidence_id}/file")
        assert get_resp.status_code == 404
        assert "Physical Evidence File" in get_resp.json()["error"]["message"]
