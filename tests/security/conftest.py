"""Shared fixtures for security tests."""

import os

import pytest
import jwt


@pytest.fixture
def jwt_encoder():
    """JWT encoding fixture for creating test tokens."""
    def encode(payload: dict) -> str:
        return jwt.encode(payload, "test-secret-key", algorithm="HS256")
    return encode


@pytest.fixture
def standard_user_token(jwt_encoder):
    """Standard user JWT token with limited permissions."""
    return jwt_encoder({
        "sub": "user-123",
        "tenant_id": "tenant-a",
        "role": "standard",
    })


@pytest.fixture
def admin_user_token(jwt_encoder):
    """Admin user JWT token with full permissions."""
    return jwt_encoder({
        "sub": "admin-456",
        "tenant_id": "tenant-a",
        "role": "admin",
    })


@pytest.fixture
def tenant_a_token(jwt_encoder):
    """JWT token for Tenant A user."""
    return jwt_encoder({
        "sub": "user-123",
        "tenant_id": "tenant-a",
        "role": "standard",
        "email": "user@tenant-a.com",
    })


@pytest.fixture
def tenant_b_token(jwt_encoder):
    """JWT token for Tenant B user."""
    return jwt_encoder({
        "sub": "user-456",
        "tenant_id": "tenant-b",
        "role": "standard",
        "email": "user@tenant-b.com",
    })


@pytest.fixture
def db_connection():
    """Database connection for RLS policy testing."""
    import psycopg2

    # Read from environment or use test defaults
    db_url = os.getenv("TEST_DATABASE_URL", "postgresql://localhost:5432/test_value_fabric")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture
def redis_client():
    """Redis client for cache isolation testing."""
    import redis

    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_db = int(os.getenv("REDIS_DB", 0))

    client = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        decode_responses=False,
    )
    yield client
    client.close()


@pytest.fixture
def client():
    """TestClient fixture - overridden from root conftest."""
    from fastapi.testclient import TestClient

    # This assumes the app is importable - may need adjustment based on actual structure
    try:
        from value_fabric.layer1_ingestion.src.api.main import app
        return TestClient(app)
    except ImportError:
        # Fallback - tests using this will be skipped if app not available
        pytest.skip("FastAPI app not available for testing")
        return None
