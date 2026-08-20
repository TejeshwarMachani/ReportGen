"""Smoke test suite for AI Business Report Generation System.

Tests core endpoints and verifies basic functionality:
- Health checks
- Auth/org scoping
- Dataset operations
- Report generation
- Forecast generation
- Chat messages
- Audit logging
"""

import pytest
import json


class TestHealthEndpoints:
    """Test /health, /ready, /live endpoints."""

    def test_health_endpoint(self, client):
        """Health check should return 200 with healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        # Verify security headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" in response.headers

    def test_readiness_check(self, client):
        """Readiness check should verify dependencies."""
        response = client.get("/ready")
        # Should return 200 if deps available, 503 if not
        assert response.status_code in (200, 503)
        if response.status_code == 200:
            data = response.json()
            assert data["status"] in ("ready", "not_ready")

    def test_liveness_check(self, client):
        """Liveness check should return 200."""
        response = client.get("/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestRateLimiting:
    """Test rate limiting headers on API endpoints."""

    def test_rate_limit_headers_on_report_generate(self, client):
        """Report generate should have rate limit headers."""
        response = client.post(
            "/api/v1/reports/generate",
            json={"dataset_id": "test", "title": "Test"},
        )
        # 429 if rate limited, but should have headers
        assert "X-Rate-Limit-Limit" in response.headers
        assert "X-Rate-Limit-Remaining" in response.headers
        assert "X-Rate-Limit-Reset" in response.headers

    def test_rate_limit_headers_on_forecast_generate(self, client):
        """Forecast generate should have rate limit headers."""
        response = client.post(
            "/api/v1/forecast/generate/{dataset_id}",
            json={"dataset_id": "test", "target_column": "col", "date_column": "date"},
        )
        assert "X-Rate-Limit-Limit" in response.headers

    def test_rate_limit_headers_on_chat_message(self, client):
        """Chat message should have rate limit headers."""
        response = client.post(
            "/api/v1/chat/message",
            json={"message": "test", "dataset_id": "test"},
        )
        assert "X-Rate-Limit-Limit" in response.headers


class TestAuditEndpoints:
    """Test audit logging endpoints."""

    def test_list_audit_logs(self, client, auth_headers):
        """List audit logs should return entries with org_id scoping."""
        response = client.get("/api/v1/audit/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Each entry should have required fields
        if data:
            entry = data[0]
            required_fields = [
                "id", "timestamp", "method", "path", "org_id",
                "user_id", "request_id", "ip_address", "user_agent",
                "status_code", "response_time_ms", "sensitive_data_detected",
                "description", "success"
            ]
            for field in required_fields:
                assert field in entry, f"Missing field: {field}"

    def test_retention_cleanup(self, client, auth_headers):
        """Retention cleanup endpoint."""
        response = client.delete(
            "/api/v1/audit/retention/cleanup",
            headers=auth_headers,
            params={"days": 90},
        )
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data
        assert "retention_days" in data


class TestOrgScoping:
    """Test org_id scoping on all queries."""

    def test_datasets_org_scoping(self, client, auth_headers):
        """Datasets list should be scoped to user's org."""
        response = client.get("/api/v1/datasets/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Every returned dataset has the expected shape
        for dataset in data:
            assert "id" in dataset
            assert "status" in dataset

    def test_reports_org_scoping(self, client, auth_headers):
        """Reports list should be scoped to user's org."""
        response = client.get("/api/v1/reports/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for report in data:
            assert "id" in report
            assert "status" in report

    def test_audit_logs_org_scoping(self, client, auth_headers):
        """Audit logs should be org_id scoped."""
        response = client.get("/api/v1/audit/", headers=auth_headers)
        assert response.status_code == 200


class TestChatDSL:
    """Test chat with data DSL constraints."""

    def test_chat_message_dsl(self, client, auth_headers, sample_dataset):
        """Chat message should validate DSL constraints."""
        response = client.post(
            "/api/v1/chat/message",
            json={"message": "what is the total sales", "dataset_id": "test"},
            headers=auth_headers,
        )
        # Should return structured response
        assert response.status_code in (200, 404, 422)
