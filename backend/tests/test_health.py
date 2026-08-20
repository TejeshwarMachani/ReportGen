"""Basic health check tests."""


def test_health_check(client):
    """Test health endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_liveness_check(client):
    """Test liveness endpoint."""
    response = client.get("/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}
    # Security headers present
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_readiness_check(client):
    """Test readiness endpoint returns a structured response (dependency state may vary)."""
    response = client.get("/ready")
    assert response.status_code in (200, 503)