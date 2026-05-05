"""Fixtures for Layer 6 security invariant tests."""

import os
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient

# Constants
DEFAULT_LAYER6_URL = "http://localhost:8006"
DEFAULT_TIMEOUT = 10.0


@pytest.fixture
def admin_token(admin_user_token: str) -> str:
    """Alias for admin_user_token to match test expectations."""
    return admin_user_token


@pytest.fixture
def tenant_a_token(jwt_token_a: str) -> str:
    """Alias for jwt_token_a to match test expectations."""
    return jwt_token_a


@pytest.fixture
def tenant_b_token(jwt_token_b: str) -> str:
    """Alias for jwt_token_b to match test expectations."""
    return jwt_token_b


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for Layer 6 API tests.
    
    Uses LAYER6_API_URL environment variable, falls back to localhost:8006.
    """
    base_url = os.getenv("LAYER6_API_URL", DEFAULT_LAYER6_URL).rstrip("/")
    timeout = float(os.getenv("CONTRACT_TEST_TIMEOUT", DEFAULT_TIMEOUT))
    
    async with AsyncClient(base_url=base_url, timeout=timeout) as client:
        yield client
