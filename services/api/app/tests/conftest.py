"""
Shared fixtures for services/api tests.

Provides:
  - mint_token(tenant_id, subject) — create a signed JWT for test requests
  - auth_headers(tenant_id, subject) — Authorization header dict
  - TENANT_ALPHA / TENANT_BETA — stable tenant IDs for isolation tests
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

# Use the same default secret the app uses in test/dev environments
TEST_SECRET = "fabric-4l-dev-secret-key-change-in-production"
TEST_ALGORITHM = "HS256"

TENANT_ALPHA = "tenant-alpha"
TENANT_BETA = "tenant-beta"


def mint_token(
    tenant_id: str = TENANT_ALPHA,
    subject: str = "test-user-001",
    expires_delta: timedelta = timedelta(hours=1),
) -> str:
    """Return a signed JWT accepted by the test app."""
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "exp": expire,
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


def auth_headers(
    tenant_id: str = TENANT_ALPHA,
    subject: str = "test-user-001",
) -> dict[str, str]:
    """Return headers dict with a valid Bearer token for the given tenant."""
    token = mint_token(tenant_id=tenant_id, subject=subject)
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id,
    }


@pytest.fixture
def alpha_headers() -> dict[str, str]:
    return auth_headers(TENANT_ALPHA)


@pytest.fixture
def beta_headers() -> dict[str, str]:
    return auth_headers(TENANT_BETA)
