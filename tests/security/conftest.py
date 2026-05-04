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


class _CallableString(str):
    """String proxy that also supports legacy ``response.text()`` calls."""

    def __call__(self) -> str:
        return str(self)


class _AwaitableResponse:
    """Proxy an HTTP response for both sync and legacy async security tests."""

    def __init__(self, response):
        self._response = response

    def __await__(self):
        async def _return_self():
            return self

        return _return_self().__await__()

    def __getattr__(self, name: str):
        if name == "text":
            return _CallableString(self._response.text)
        return getattr(self._response, name)


class _HybridTestClient:
    """Expose TestClient methods that work with or without ``await``."""

    def __init__(self, client):
        self._client = client

    def __getattr__(self, name: str):
        return getattr(self._client, name)

    def _wrap(self, response):
        return _AwaitableResponse(response)

    def get(self, *args, **kwargs):
        return self._wrap(self._client.get(*args, **kwargs))

    def post(self, *args, **kwargs):
        return self._wrap(self._client.post(*args, **kwargs))

    def put(self, *args, **kwargs):
        return self._wrap(self._client.put(*args, **kwargs))

    def patch(self, *args, **kwargs):
        return self._wrap(self._client.patch(*args, **kwargs))

    def delete(self, *args, **kwargs):
        return self._wrap(self._client.delete(*args, **kwargs))

    def options(self, *args, **kwargs):
        return self._wrap(self._client.options(*args, **kwargs))


@pytest.fixture
def client():
    """Hybrid L1 ingestion API client for sync and async security tests."""
    TestClient = _get_testclient()
    if TestClient is None:
        pytest.skip("fastapi not installed")
    
    try:
        from value_fabric.layer1.api.main import app
        return _HybridTestClient(TestClient(app))
    except ImportError:
        pytest.skip("FastAPI app not available for testing")


@pytest.fixture
def expired_token(jwt_encoder) -> str:
    """Expired JWT token for negative testing."""
    import time
    return jwt_encoder({
        "sub": "user-123",
        "tenant_id": "tenant-a",
        "role": "standard",
        "exp": int(time.time()) - 3600,  # Expired 1 hour ago
    })


@pytest.fixture
def invalid_signature_token() -> str:
    """Token with invalid signature for negative testing."""
    # Create a valid-looking token but sign with wrong secret
    payload = {
        "sub": "user-123",
        "tenant_id": "tenant-a",
        "role": "standard",
    }
    return jwt.encode(payload, "wrong-secret", algorithm="HS256")


@pytest.fixture
def malformed_token() -> str:
    """Completely malformed token."""
    return "not.a.valid.jwt.token"


@pytest.fixture
def auth_headers(auth_headers_a):
    """Legacy alias for Tenant A JWT auth headers used by older security suites."""
    return dict(auth_headers_a)


@pytest.fixture
def user_headers(auth_headers_a):
    """Legacy alias for standard-user JWT auth headers used by older security suites."""
    return dict(auth_headers_a)


@pytest.fixture
def admin_headers(auth_headers_admin):
    """Legacy alias for admin JWT auth headers used by older security suites."""
    return dict(auth_headers_admin)


@pytest.fixture
def websocket_client():
    """TestClient fixture for L4 WebSocket testing."""
    TestClient = _get_testclient()
    if TestClient is None:
        pytest.skip("fastapi not installed")
    
    try:
        # Try to import L4 app - may not be available without dependencies
        from value_fabric.layer4.api.main import app
        return TestClient(app)
    except ImportError:
        pytest.skip("Layer 4 FastAPI app not available for WebSocket testing")
