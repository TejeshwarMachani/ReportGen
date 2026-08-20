"""Basic health check tests."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health endpoint returns 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test readiness endpoint."""
    response = await client.get("/ready")
    # Should be ready if dependencies are up
    assert response.status_code in (200, 503)


@pytest.mark.asyncio
async def test_liveness_check(client: AsyncClient):
    """Test liveness endpoint."""
    response = await client.get("/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}