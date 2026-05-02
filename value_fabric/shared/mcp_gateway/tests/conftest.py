"""Shared pytest fixtures for all MCP Gateway test layers.

This conftest.py is at the tests/ root and provides fixtures used across
unit, contract, integration, security, resilience, and performance tests.
"""

from __future__ import annotations

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

# Import gateway components
from shared.mcp_gateway import (
    MCPGateway,
    OAuthHandler,
    TokenExchanger,
    ManifestVerifier,
    ToolRegistry,
    PKCEVerifier,
)
from shared.mcp_gateway.mcp_types import (
    ToolManifest,
    OAuthClientConfig,
    ToolRequest,
    ToolResponse,
    DelegatedToken,
    AuthenticationError,
    ManifestValidationError,
    ToolAccessDeniedError,
    PKCEChallenge,
)
from shared.models.typed_dict import TypedDictModel


class sample_rsa_keypairResult(TypedDictModel):
    key_id: str
    private: str
    public: str


# =============================================================================
# Identity Fixtures
# =============================================================================

@pytest.fixture
def sample_tenant_id() -> str:
    """Sample tenant UUID for testing."""
    return str(uuid4())


@pytest.fixture
def sample_user_id() -> str:
    """Sample user identifier."""
    return "user-test-123"


@pytest.fixture
def sample_trace_id() -> str:
    """Sample trace ID for observability testing."""
    return f"trace-{uuid4().hex[:16]}"


# =============================================================================
# Token Fixtures
# =============================================================================

@pytest.fixture
def sample_user_token() -> str:
    """Valid-format JWT for testing (cryptographically invalid, for parsing tests).
    
    Structure: header.payload.signature (base64url encoded)
    """
    # Valid JWT structure with realistic claims
    header = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5LTEifQ"
    payload = (
        "eyJzdWIiOiJ1c2VyLXRlc3QtMTIzIiwibmFtZSI6IlRlc3QgVXNlciIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIs"
        "Im9yZ19pZCI6InRlbmFudC1hYmMtMTIzIiwic2NvcGUiOiJ0b29sczpyZWFkIHRvb2xzOndyaXRlIiwiaWF0IjoxNzE0"
        "MDAwMDAwLCJleHAiOjE3MTQwODY0MDAsImp0aSI6InRva2VuLTEyMyJ9"
    )
    signature = "mock-signature-for-testing-only"
    return f"{header}.{payload}.{signature}"


@pytest.fixture
def sample_expired_token() -> str:
    """Token with expired claims."""
    header = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9"
    # Payload with exp in the past (exp: 1600000000 = Sep 2020)
    payload = (
        "eyJzdWIiOiJ1c2VyLXRlc3QtMTIzIiwic2NvcGUiOiJ0b29sczpyZWFkIiwiaWF0IjoxNTk5OTk5MDAwLCJleHAiOjE2"
        "MDAwMDAwMDB9"
    )
    return f"{header}.{payload}.expired-sig"


@pytest.fixture
def sample_delegated_token() -> DelegatedToken:
    """Sample delegated token for tool invocation."""
    return DelegatedToken(
        access_token="delegated-token-abc123",
        token_type="Bearer",
        expires_in=3600,
        scope="tools:search:read",
        tool_name="search",
        issued_at=datetime.utcnow(),
    )


# =============================================================================
# Tool Manifest Fixtures
# =============================================================================

@pytest.fixture
def sample_tool_manifest() -> ToolManifest:
    """Sample tool manifest for testing."""
    return ToolManifest(
        tool_name="test_search",
        description=(
            "Search across documents. Use this when you need to find information "
            "in the knowledge base. Returns matching documents with relevance scores."
        ),
        version="1.0.0",
        input_schema={
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string (1-200 characters)",
                    "minLength": 1,
                    "maxLength": 200,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return (1-100, default 10)",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10,
                },
            },
            "additionalProperties": False,
        },
        required_permissions=["search:read"],
        tenant_scoped=True,
        timeout_ms=30000,
        supports_partial=False,
    )


@pytest.fixture
def sample_tool_manifests() -> list[ToolManifest]:
    """Multiple tool manifests for multi-upstream testing."""
    return [
        ToolManifest(
            tool_name="search",
            description="Search documents. Use this to find information by query.",
            version="1.0.0",
            input_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "additionalProperties": False,
            },
            required_permissions=["search:read"],
            tenant_scoped=True,
            timeout_ms=30000,
            supports_partial=False,
        ),
        ToolManifest(
            tool_name="calculate",
            description="Perform calculations. Use for math operations.",
            version="1.0.0",
            input_schema={
                "type": "object",
                "required": ["expression"],
                "properties": {
                    "expression": {"type": "string", "description": "Math expression to evaluate"}
                },
                "additionalProperties": False,
            },
            required_permissions=["tools:execute"],
            tenant_scoped=True,
            timeout_ms=10000,
            supports_partial=False,
        ),
        ToolManifest(
            tool_name="validate",
            description="Validate data against schema. Use for data quality checks.",
            version="2.0.0",
            input_schema={
                "type": "object",
                "required": ["data", "schema"],
                "properties": {
                    "data": {"type": "object", "description": "Data to validate"},
                    "schema": {"type": "string", "description": "Schema name or JSON schema"},
                },
                "additionalProperties": False,
            },
            required_permissions=["validate:read", "validate:execute"],
            tenant_scoped=True,
            timeout_ms=15000,
            supports_partial=False,
        ),
    ]


# =============================================================================
# OAuth Configuration Fixtures
# =============================================================================

@pytest.fixture
def sample_oauth_config() -> OAuthClientConfig:
    """Sample OAuth 2.1 + PKCE configuration."""
    return OAuthClientConfig(
        client_id="test-client-123",
        client_secret="test-secret-456",
        authorization_endpoint="https://auth.example.com/oauth2/authorize",
        token_endpoint="https://auth.example.com/oauth2/token",
        redirect_uri="https://gateway.example.com/auth/callback",
        scopes=["openid", "profile", "tools:read", "tools:write"],
    )


@pytest.fixture
def sample_pkce_challenge() -> PKCEChallenge:
    """Sample PKCE challenge for OAuth testing."""
    return PKCEVerifier.generate_challenge()


# =============================================================================
# Gateway Component Fixtures
# =============================================================================

@pytest.fixture
def mock_auth_handler() -> Mock:
    """Mocked OAuth handler for unit tests."""
    handler = Mock(spec=OAuthHandler)
    handler.get_authorization_url = Mock(return_value=(
        "https://auth.example.com/authorize?client_id=test&redirect_uri=callback",
        "state-abc123"
    ))
    handler.exchange_code = AsyncMock(return_value={
        "access_token": "mock-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    })
    return handler


@pytest.fixture
def mock_token_exchanger() -> Mock:
    """Mocked token exchanger for unit tests."""
    exchanger = Mock(spec=TokenExchanger)
    exchanger.exchange_for_tool = AsyncMock(return_value=DelegatedToken(
        access_token="delegated-mock-token",
        token_type="Bearer",
        expires_in=3600,
        scope="tools:read",
        tool_name="test_tool",
        issued_at=datetime.utcnow(),
    ))
    return exchanger


@pytest.fixture
def mock_manifest_verifier() -> Mock:
    """Mocked manifest verifier for unit tests."""
    verifier = Mock(spec=ManifestVerifier)
    verifier.verify_manifest = Mock(return_value=True)
    return verifier


@pytest.fixture
def sample_tool_registry() -> ToolRegistry:
    """Pre-configured tool registry with sample tools."""
    registry = ToolRegistry()
    
    # Register some sample tools
    for manifest in [
        ToolManifest(
            tool_name="test_search",
            description="Search tool for testing",
            version="1.0.0",
            input_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "description": "Query"}
                },
                "additionalProperties": False,
            },
            required_permissions=["search:read"],
            tenant_scoped=True,
            timeout_ms=30000,
            supports_partial=False,
        ),
        ToolManifest(
            tool_name="test_calculate",
            description="Calculate tool for testing",
            version="1.0.0",
            input_schema={
                "type": "object",
                "required": ["expression"],
                "properties": {
                    "expression": {"type": "string", "description": "Math expression"}
                },
                "additionalProperties": False,
            },
            required_permissions=["tools:execute"],
            tenant_scoped=True,
            timeout_ms=10000,
            supports_partial=False,
        ),
    ]:
        registry.register_tool(manifest, verified=True)
    
    return registry


# =============================================================================
# Gateway Fixtures
# =============================================================================

@pytest.fixture
def mock_gateway(
    mock_auth_handler: Mock,
    mock_token_exchanger: Mock,
    mock_manifest_verifier: Mock,
    sample_tool_registry: ToolRegistry,
) -> MCPGateway:
    """Gateway with fully mocked dependencies for unit testing."""
    return MCPGateway(
        auth_handler=mock_auth_handler,
        token_exchanger=mock_token_exchanger,
        manifest_verifier=mock_manifest_verifier,
        tool_registry=sample_tool_registry,
        enable_audit_logging=False,  # Disable for unit tests
    )


@pytest.fixture
def minimal_gateway() -> MCPGateway:
    """Gateway with minimal/no dependencies for basic testing."""
    return MCPGateway(
        auth_handler=None,
        token_exchanger=None,
        manifest_verifier=None,
        tool_registry=ToolRegistry(),
        enable_audit_logging=False,
    )


# =============================================================================
# Request/Response Fixtures
# =============================================================================

@pytest.fixture
def sample_tool_request() -> ToolRequest:
    """Sample tool invocation request."""
    return ToolRequest(
        tool_name="test_search",
        parameters={"query": "test query", "limit": 10},
        tenant_id=uuid4(),
        user_id="user-test-123",
        request_id=f"req-{uuid4().hex[:12]}",
        parent_span_id=None,
    )


@pytest.fixture
def sample_tool_response() -> ToolResponse:
    """Sample successful tool response."""
    return ToolResponse(
        tool_name="test_search",
        result={
            "results": [
                {"id": "doc-1", "title": "Test Document", "score": 0.95}
            ],
            "total": 1,
        },
        error=None,
        execution_time_ms=145.5,
        request_id=f"req-{uuid4().hex[:12]}",
        audit_event_id=f"audit-{uuid4().hex[:12]}",
    )


# =============================================================================
# Cryptographic Fixtures
# =============================================================================

@pytest.fixture
def sample_rsa_keypair() -> dict:
    """Sample RSA keypair for JWS manifest testing.
    
    These are mock keys for testing only - do not use in production!
    """
    # In real implementation, these would be actual RSA keys
    # For unit tests, we use placeholder strings that represent key material
    return sample_rsa_keypairResult.model_validate({
        "private": "mock-private-key-for-testing-only-do-not-use-in-production",
        "public": "mock-public-key-for-testing-only-do-not-use-in-production",
        "key_id": "test-key-001",
    })


# =============================================================================
# Async Configuration
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Pytest Configuration Hooks
# =============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Pure unit tests, no external dependencies")
    config.addinivalue_line("markers", "contract: Protocol compliance with canned fixtures")
    config.addinivalue_line("markers", "integration: Docker-based tests with real MCP servers")
    config.addinivalue_line("markers", "security: Security abuse cases and threat tests")
    config.addinivalue_line("markers", "resilience: Fault injection and degradation tests")
    config.addinivalue_line("markers", "performance: Load, latency, and soak tests")
    config.addinivalue_line("markers", "asyncio: Async test support")
    config.addinivalue_line("markers", "slow: Tests taking >5 seconds")
    config.addinivalue_line("markers", "http: Streamable HTTP transport tests")
    config.addinivalue_line("markers", "stdio: STDIO transport tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on path."""
    for item in items:
        # Auto-add markers based on test file location
        path = str(item.fspath)
        if "/unit/" in path and not any(item.iter_markers("unit")):
            item.add_marker(pytest.mark.unit)
        elif "/contract/" in path and not any(item.iter_markers("contract")):
            item.add_marker(pytest.mark.contract)
        elif "/integration/" in path and not any(item.iter_markers("integration")):
            item.add_marker(pytest.mark.integration)
        elif "/security/" in path and not any(item.iter_markers("security")):
            item.add_marker(pytest.mark.security)
        elif "/resilience/" in path and not any(item.iter_markers("resilience")):
            item.add_marker(pytest.mark.resilience)
        elif "/performance/" in path and not any(item.iter_markers("performance")):
            item.add_marker(pytest.mark.performance)
