import os
import sys
from pathlib import Path

# Belt-and-braces: ensure repo root is on sys.path so `value_fabric.layer6.*`
# canonical-shim imports resolve even if pyproject.toml `pythonpath` is bypassed
# (e.g. ad-hoc invocations outside the configured pytest session).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pytest
from unittest.mock import AsyncMock

_TEST_ENV_DEFAULTS = {
    "ENVIRONMENT": "test",
    "APP_ENV": "test",
    "TESTING": "true",
    "NEO4J_URI": "bolt://localhost:7687",
    "NEO4J_USER": "neo4j",
    "NEO4J_PASSWORD": "test_password",
    "ALLOW_INSECURE_DEV_AUTH_BYPASS": "true",
    "DEV_AUTH_BYPASS": "true",
    "ALLOW_DEV_AUTH_BYPASS": "I_UNDERSTAND_RISK",
    # Match root conftest.py secret defaults so L6 service venv can boot the FastAPI
    # app without a live Infisical / vault. Mirrors the canonical test-secret values
    # required by value_fabric.shared.secrets.infisical._validate_required_secrets.
    "JWT_SECRET": "dummy_jwt_secret_for_tests_must_be_32_chars",
    "API_KEY_HMAC_SECRET": "dummy_api_key_secret_for_tests_must_be_32_chars",
    "SERVICE_AUTH_SECRET": "dummy_service_auth_secret_for_tests_32_chars",
    "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/fabric",
}
for _key, _value in _TEST_ENV_DEFAULTS.items():
    os.environ.setdefault(_key, _value)

import src.database as database
from value_fabric.shared.identity.middleware import GovernanceMiddleware

@pytest.fixture(autouse=True)
def mock_governance_middleware(monkeypatch):
    """Bypass the actual JWT validation in GovernanceMiddleware for tests.
    We rely on app.dependency_overrides[get_request_context] in the test client
    to control the actual tenant_id seen by the endpoints."""
    async def mock_dispatch(self, request, call_next):
        from value_fabric.shared.identity.context import RequestContext
        from uuid import uuid4
        
        # Give it a fallback context just in case, though get_request_context should override it
        ctx = RequestContext(
            tenant_id="system",
            user_id=uuid4(),
            org_id=uuid4(),
            roles=["admin"],
            permissions=[],
            auth_source="mock",
            tenant_role="admin",
            isolation_tier="shared",
            request_id="test"
        )
        request.state.governance_context = ctx
        from value_fabric.shared.identity.context import set_request_context
        set_request_context(ctx)
        return await call_next(request)
        
    monkeypatch.setattr(GovernanceMiddleware, "dispatch", mock_dispatch)

@pytest.fixture(autouse=True)
def mock_neo4j_health(monkeypatch):
    """Mock Neo4j health check to avoid real DB connections."""
    async def mock_health(*args, **kwargs):
        return {"status": "healthy"}
    
    monkeypatch.setattr(database, "health_check", mock_health)
    # Also patch the actual neo4j_health_check imported in main
    import src.api.main as main_module
    monkeypatch.setattr(main_module, "neo4j_health_check", mock_health)

