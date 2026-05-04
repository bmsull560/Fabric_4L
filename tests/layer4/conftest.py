"""Fixtures for Layer 4 security invariant tests."""

import os
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient

# Import fixtures from security conftest
pytest_plugins = ["tests.security.conftest"]

# Constants
DEFAULT_LAYER4_URL = "http://localhost:8004"
DEFAULT_TIMEOUT = 10.0


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for Layer 4 API tests.
    
    Uses LAYER4_API_URL environment variable, falls back to localhost:8004.
    """
    base_url = os.getenv("LAYER4_API_URL", DEFAULT_LAYER4_URL).rstrip("/")
    timeout = float(os.getenv("CONTRACT_TEST_TIMEOUT", DEFAULT_TIMEOUT))
    
    async with AsyncClient(base_url=base_url, timeout=timeout) as client:
        yield client
