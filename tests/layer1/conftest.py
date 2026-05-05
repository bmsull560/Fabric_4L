"""Fixtures for Layer 1 security invariant tests."""

import os
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Constants
DEFAULT_LAYER1_URL = "http://localhost:8001"
DEFAULT_TIMEOUT = 10.0


@pytest.fixture
def admin_token(admin_user_token: str) -> str:
    """Alias for admin_user_token to match test expectations."""
    return admin_user_token


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for Layer 1 API tests.
    
    Uses LAYER1_API_URL environment variable, falls back to localhost:8001.
    """
    base_url = os.getenv("LAYER1_API_URL", DEFAULT_LAYER1_URL).rstrip("/")
    timeout = float(os.getenv("CONTRACT_TEST_TIMEOUT", DEFAULT_TIMEOUT))
    
    async with AsyncClient(base_url=base_url, timeout=timeout) as client:
        yield client


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Database session for RLS policy verification tests.
    
    This fixture requires PostgreSQL to be running.
    Skips tests if the integration conftest is not available.
    """
    try:
        from tests.integration.conftest import db_session as integration_db_session
    except ImportError:
        pytest.skip("db_session fixture not available - integration tests not configured")
        return  # Never reached, but satisfies type checker
    
    async for session in integration_db_session():
        yield session
