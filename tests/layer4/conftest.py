"""Fixtures for Layer 4 security invariant tests."""

import pytest
from httpx import AsyncClient

# Import fixtures from security conftest
pytest_plugins = ["tests.security.conftest"]


@pytest.fixture
async def client() -> AsyncClient:
    """Async HTTP client for Layer 4 API tests.
    
    Uses LAYER4_API_URL environment variable, falls back to localhost:8004.
    """
    import os
    
    base_url = os.getenv("LAYER4_API_URL", "http://localhost:8004").rstrip("/")
    timeout = float(os.getenv("CONTRACT_TEST_TIMEOUT", "10.0"))
    
    async with AsyncClient(base_url=base_url, timeout=timeout) as client:
        yield client
