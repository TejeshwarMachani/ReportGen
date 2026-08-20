"""Pytest configuration and fixtures."""
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "postgresql+psycopg2://test:test@localhost:5432/reportgen_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SECRET_KEY"] = "test-secret-key-for-ci-1234567890abcdef"
os.environ["ANTHROPIC_API_KEY"] = "dummy-key-for-testing"
os.environ["ENVIRONMENT"] = "testing"

from app.main import app
from app.database import Base, get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def client():
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac