"""Shared fixtures for security tests."""

import os
from typing import Callable, Generator

import pytest
import jwt
import psycopg2
import redis
from fastapi.testclient import TestClient

# Test configuration constants
TEST_JWT_SECRET = os.getenv("TEST_JWT_SECRET", "test-secret-key")
DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_DB = 0


@pytest.fixture
def jwt_encoder() -> Callable[[dict], str]:
    """JWT encoding fixture for creating test tokens."""
    def encode(payload: dict) -> str:
        return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
    return encode


@pytest.fixture
def standard_user_token(jwt_encoder) -> str:
    """Standard user JWT token with limited permissions."""
    return jwt_encoder({
        "sub": "user-123",
        "tenant_id": "tenant-a",
        "role": "standard",
    })


@pytest.fixture
def admin_user_token(jwt_encoder) -> str:
    """Admin user JWT token with full permissions."""
    return jwt_encoder({
        "sub": "admin-456",
        "tenant_id": "tenant-a",
        "role": "admin",
    })


@pytest.fixture
def tenant_a_token(jwt_encoder) -> str:
    """JWT token for Tenant A user."""
    return jwt_encoder({
        "sub": "user-123",
        "tenant_id": "tenant-a",
        "role": "standard",
        "email": "user@tenant-a.com",
    })


@pytest.fixture
def tenant_b_token(jwt_encoder) -> str:
    """JWT token for Tenant B user."""
    return jwt_encoder({
        "sub": "user-456",
        "tenant_id": "tenant-b",
        "role": "standard",
        "email": "user@tenant-b.com",
    })


@pytest.fixture
def db_connection() -> Generator:
    """Database connection for RLS policy testing."""
    db_url = os.getenv("TEST_DATABASE_URL", "postgresql://localhost:5432/test_value_fabric")

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        yield conn
    except psycopg2.OperationalError as e:
        pytest.skip(f"Database not available for RLS testing: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()


@pytest.fixture
def redis_client() -> Generator:
    """Redis client for cache isolation testing."""
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", DEFAULT_REDIS_PORT))
    redis_db = int(os.getenv("REDIS_DB", DEFAULT_REDIS_DB))

    try:
        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=False,
        )
        # Test connection before yielding
        client.ping()
        yield client
    except redis.ConnectionError as e:
        pytest.skip(f"Redis not available for cache isolation testing: {e}")
    finally:
        if 'client' in locals() and client:
            client.close()


@pytest.fixture
def client() -> TestClient:
    """TestClient fixture - overridden from root conftest."""
    try:
        from layer1_ingestion.src.api.main import app
        return TestClient(app)
    except ImportError:
        pytest.skip("FastAPI app not available for testing")
