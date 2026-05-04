"""Fixtures for Layer 1 security invariant tests."""

import pytest
from httpx import AsyncClient

# Import fixtures from security conftest
pytest_plugins = ["tests.security.conftest"]

# Re-export with correct names for consistency
@pytest.fixture
def admin_token(admin_user_token: str) -> str:
    """Alias for admin_user_token to match test expectations."""
    return admin_user_token


@pytest.fixture
async def client() -> AsyncClient:
    """Async HTTP client for Layer 1 API tests.
    
    Uses LAYER1_API_URL environment variable, falls back to localhost:8001.
    """
    import os
    
    base_url = os.getenv("LAYER1_API_URL", "http://localhost:8001").rstrip("/")
    timeout = float(os.getenv("CONTRACT_TEST_TIMEOUT", "10.0"))
    
    async with AsyncClient(base_url=base_url, timeout=timeout) as client:
        yield client


@pytest.fixture
async def db_session():
    """Database session for RLS policy verification tests.
    
    This fixture requires PostgreSQL to be running.
    """
    # Import from integration conftest if available, otherwise skip
    try:
        from tests.integration.conftest import db_session as integration_db_session
        async for session in integration_db_session():
            yield session
    except (ImportError, AttributeError):
        pytest.skip("db_session fixture not available - requires integration test setup")
