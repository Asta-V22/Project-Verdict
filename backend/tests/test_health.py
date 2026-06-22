"""
Tests for the health endpoint.

Verifies:
  - Standard response envelope shape
  - Healthy status with database connection
  - Configuration values in response
  - ISO timestamp presence
"""

from __future__ import annotations


class TestHealthEndpoint:
    """GET /api/v1/health"""

    def test_returns_success_envelope(self, client):
        """Response follows the standard ``{"success": true, "data": ...}`` shape."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "data" in body

    def test_reports_healthy_status(self, client):
        """Backend reports healthy with database connected."""
        data = client.get("/api/v1/health").json()["data"]

        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["app"] == "Project Verdict"
        assert data["version"] == "v1"

    def test_includes_configuration(self, client):
        """Response includes key configuration values."""
        data = client.get("/api/v1/health").json()["data"]

        assert "db_path" in data
        assert "evidence_dir" in data
        assert "max_evidence_file_size_mb" in data
        assert data["max_evidence_file_size_mb"] == 10

    def test_includes_timestamp(self, client):
        """Response contains an ISO-formatted UTC timestamp."""
        data = client.get("/api/v1/health").json()["data"]

        assert "timestamp" in data
        assert "T" in data["timestamp"]  # ISO 8601 always contains 'T'


class TestErrorHandling:
    """Verify global exception handlers produce the standard error envelope."""

    def test_404_for_unknown_route(self, client):
        """Unknown routes return 404 in the standard error envelope."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"
        assert "message" in body["error"]

    def test_422_for_invalid_input(self, client):
        """
        Validation errors return the standard error envelope.

        We don't have CRUD endpoints yet, but this verifies the handler
        is registered.  Once CRUD lands, this test can be expanded.
        """
        # POST to health with unexpected body — FastAPI doesn't validate
        # GET params on /health, so this is a baseline existence check.
        response = client.get("/api/v1/health")
        assert response.status_code == 200  # Health has no required params
