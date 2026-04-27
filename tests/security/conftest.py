"""Shared fixtures for security tests."""

import os
from typing import Callable, Generator

import pytest
import jwt

# Lazy imports for optional dependencies
def _get_psycopg2():
    try:
        import psycopg2
        return psycopg2
    except ImportError:
        return None

def _get_redis():
    try:
        import redis
        return redis
    except ImportError:
        return None

def _get_testclient():
    try:
        from fastapi.testclient import TestClient
        return TestClient
    except ImportError:
        return None

# Test configuration constants
# JWT_SECRET is the canonical env var name used across CI and all layers
TEST_JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("TEST_JWT_SECRET", "test-secret-key"))
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


def check_db() -> bool:
    """Check if database is available."""
    psycopg2 = _get_psycopg2()
    if psycopg2 is None:
        return False
    db_url = os.getenv("TEST_DATABASE_URL", "postgresql://localhost:5432/test_value_fabric")
    try:
        conn = psycopg2.connect(db_url)
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False


def check_redis() -> bool:
    """Check if Redis is available."""
    redis = _get_redis()
    if redis is None:
        return False
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    try:
        client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=False)
        client.ping()
        client.close()
        return True
    except redis.ConnectionError:
        return False


@pytest.fixture(scope="session")
def require_security_deps():
    """Ensure security test dependencies are available - hard fail in CI."""
    if os.getenv("CI") == "true":
        # In CI, hard requirements
        assert check_db(), "Security tests require DB in CI"
        assert check_redis(), "Security tests require Redis in CI"
    # Return silently in non-CI mode


@pytest.fixture
def db_connection() -> Generator:
    """Database connection for RLS policy testing."""
    psycopg2 = _get_psycopg2()
    if psycopg2 is None:
        pytest.skip("psycopg2 not installed")
    
    db_url = os.getenv("TEST_DATABASE_URL", "postgresql://localhost:5432/test_value_fabric")

    if os.getenv("CI") == "true":
        # In CI, hard fail
        if not check_db():
            raise RuntimeError("Security tests require DB. Run: docker-compose up postgres")

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        yield conn
    except psycopg2.OperationalError as e:
        if os.getenv("CI") == "true":
            raise RuntimeError(f"Security tests require DB in CI: {e}")
        pytest.skip(f"Database not available for RLS testing: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()


@pytest.fixture
def redis_client() -> Generator:
    """Redis client for cache isolation testing."""
    redis = _get_redis()
    if redis is None:
        pytest.skip("redis not installed")
    
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", DEFAULT_REDIS_PORT))
    redis_db = int(os.getenv("REDIS_DB", DEFAULT_REDIS_DB))

    if os.getenv("CI") == "true" and not check_redis():
        raise RuntimeError("Security tests require Redis. Run: docker-compose up redis")

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
        if os.getenv("CI") == "true":
            raise RuntimeError(f"Security tests require Redis in CI: {e}")
        pytest.skip(f"Redis not available for cache isolation testing: {e}")
    finally:
        if 'client' in locals() and client:
            client.close()


@pytest.fixture
def client():
    """TestClient fixture - L1 ingestion API client for security tests."""
    TestClient = _get_testclient()
    if TestClient is None:
        pytest.skip("fastapi not installed")
    
    import sys
    from pathlib import Path

    # Add L1 src to path for direct imports (matches pattern in test_model_registry_integration.py)
    l1_src = str(Path(__file__).resolve().parents[2] / "value-fabric" / "layer1-ingestion" / "src")
    if l1_src not in sys.path:
        sys.path.insert(0, l1_src)

    try:
        from api.main import app
        return TestClient(app)
    except ImportError:
        pytest.skip("FastAPI app not available for testing")
    finally:
        # Cleanup: remove path modification to prevent isolation leakage
        if l1_src in sys.path:
            sys.path.remove(l1_src)
