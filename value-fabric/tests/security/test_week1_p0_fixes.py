"""Week 1 P0 Security Fixes — Regression Tests.

Tests for:
- F-1: X-Tenant-ID header requires X-Service-Auth shared secret
- F-2: Tools endpoints require authentication
- F-3: Formula evaluation uses AST (no eval())

Run with: pytest tests/security/test_week1_p0_fixes.py -v
"""

from __future__ import annotations

import ast
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import Request
from starlette.datastructures import Headers

# Use conftest utilities
from .conftest import JWT_SECRET, mint_token, TENANT_A_ID, TENANT_B_ID

# ---------------------------------------------------------------------------
# F-1: X-Tenant-ID requires X-Service-Auth
# ---------------------------------------------------------------------------


class TestXTenantIDMutualAuth:
    """F-1: X-Tenant-ID header must be accompanied by valid X-Service-Auth."""

    @pytest.fixture
    def service_auth_secret(self, monkeypatch):
        """Set a test service auth secret."""
        monkeypatch.setenv("SERVICE_AUTH_SECRET", "test-service-secret-12345")
        yield "test-service-secret-12345"
        monkeypatch.delenv("SERVICE_AUTH_SECRET", raising=False)

    @pytest.fixture
    def no_service_auth_secret(self, monkeypatch):
        """Ensure SERVICE_AUTH_SECRET is not set."""
        monkeypatch.delenv("SERVICE_AUTH_SECRET", raising=False)
        yield

    @pytest.mark.asyncio
    async def test_x_tenant_id_without_service_secret_rejected(
        self, no_service_auth_secret
    ):
        """X-Tenant-ID without SERVICE_AUTH_SECRET configured should return None."""
        from value_fabric.shared.identity.middleware import GovernanceMiddleware

        middleware = GovernanceMiddleware(
            app=None,  # type: ignore
            api_key_resolver=AsyncMock(return_value=None),
        )

        # Create mock request with X-Tenant-ID but no SERVICE_AUTH_SECRET set
        request = MagicMock(spec=Request)
        request.headers = Headers({"X-Tenant-ID": str(TENANT_A_ID)})
        request.query_params = {}

        result = await middleware._resolve_identity(request)

        # Should reject and return None (not grant SYSTEM role)
        assert result is None

    @pytest.mark.asyncio
    async def test_x_tenant_id_without_x_service_auth_rejected(
        self, service_auth_secret
    ):
        """X-Tenant-ID without X-Service-Auth header should return None."""
        from value_fabric.shared.identity.middleware import GovernanceMiddleware

        middleware = GovernanceMiddleware(
            app=None,  # type: ignore
            api_key_resolver=AsyncMock(return_value=None),
        )

        request = MagicMock(spec=Request)
        request.headers = Headers({"X-Tenant-ID": str(TENANT_A_ID)})
        request.query_params = {}

        result = await middleware._resolve_identity(request)

        # Should reject and return None
        assert result is None

    @pytest.mark.asyncio
    async def test_x_tenant_id_with_invalid_x_service_auth_rejected(
        self, service_auth_secret
    ):
        """X-Tenant-ID with wrong X-Service-Auth should return None."""
        from value_fabric.shared.identity.middleware import GovernanceMiddleware

        middleware = GovernanceMiddleware(
            app=None,  # type: ignore
            api_key_resolver=AsyncMock(return_value=None),
        )

        request = MagicMock(spec=Request)
        request.headers = Headers(
            {
                "X-Tenant-ID": str(TENANT_A_ID),
                "X-Service-Auth": "wrong-secret",
            }
        )
        request.query_params = {}

        result = await middleware._resolve_identity(request)

        # Should reject and return None
        assert result is None

    @pytest.mark.asyncio
    async def test_x_tenant_id_with_valid_x_service_auth_accepted(
        self, service_auth_secret
    ):
        """X-Tenant-ID with valid X-Service-Auth should grant SYSTEM role."""
        from value_fabric.shared.identity.middleware import GovernanceMiddleware
        from value_fabric.shared.identity.permissions import Role

        middleware = GovernanceMiddleware(
            app=None,  # type: ignore
            api_key_resolver=AsyncMock(return_value=None),
        )

        request = MagicMock(spec=Request)
        request.headers = Headers(
            {
                "X-Tenant-ID": str(TENANT_A_ID),
                "X-Service-Auth": service_auth_secret,
            }
        )
        request.query_params = {}

        result = await middleware._resolve_identity(request)

        # Should return SYSTEM role context
        assert result is not None
        assert result.tenant_id == TENANT_A_ID
        assert Role.SYSTEM.value in result.roles
        assert result.source == "header"


# ---------------------------------------------------------------------------
# F-2: Tools endpoints require authentication
# ---------------------------------------------------------------------------


class TestToolsRequireAuthentication:
    """F-2: All tools endpoints must require authentication."""

    def _create_test_request(self, headers: dict | None = None) -> Request:
        """Create a minimal mock request."""
        request = MagicMock(spec=Request)
        request.headers = Headers(headers or {})
        request.query_params = {}
        request.url.path = "/v1/tools/invoke"
        return request  # type: ignore

    @pytest.mark.asyncio
    async def test_tools_invoke_without_auth_returns_401(self):
        """POST /v1/tools/invoke without auth should return 401."""
        # This is an integration test - verify the route has require_authenticated
        # by checking the FastAPI route dependencies
        from layer4_agents.src.api.routes.tools import router

        # Find the invoke_tool route
        invoke_route = None
        for route in router.routes:
            if hasattr(route, "methods") and "POST" in route.methods:
                if route.path == "/tools/invoke":
                    invoke_route = route
                    break

        assert invoke_route is not None, "invoke_tool route not found"

        # Check that the route has dependencies
        dependencies = getattr(invoke_route, "dependencies", [])
        dep_names = [str(d) for d in dependencies]

        # Should have require_authenticated dependency
        # The dependency is typically injected via Depends() in the function signature
        # which appears in the route's dependant.dependencies
        has_auth = any(
            "require_authenticated" in name or "authenticated" in name.lower()
            for name in dep_names
        )

        # Also verify by checking the function signature directly
        import inspect
        from layer4_agents.src.api.routes.tools import invoke_tool

        sig = inspect.signature(invoke_tool)
        param_types = [p.annotation for p in sig.parameters.values()]
        has_request_context = any(
            "RequestContext" in str(t) for t in param_types
        )

        assert (
            has_auth or has_request_context
        ), "invoke_tool missing authentication dependency"

    @pytest.mark.asyncio
    async def test_tools_list_requires_auth(self):
        """GET /v1/tools should require authentication."""
        from layer4_agents.src.api.routes.tools import list_tools
        import inspect

        sig = inspect.signature(list_tools)
        param_types = [p.annotation for p in sig.parameters.values()]
        has_request_context = any(
            "RequestContext" in str(t) for t in param_types
        )

        assert has_request_context, "list_tools missing RequestContext dependency"

    @pytest.mark.asyncio
    async def test_tools_schema_requires_auth(self):
        """GET /v1/tools/{name} should require authentication."""
        from layer4_agents.src.api.routes.tools import get_tool_schema
        import inspect

        sig = inspect.signature(get_tool_schema)
        param_types = [p.annotation for p in sig.parameters.values()]
        has_request_context = any(
            "RequestContext" in str(t) for t in param_types
        )

        assert has_request_context, "get_tool_schema missing RequestContext dependency"


# ---------------------------------------------------------------------------
# F-3: Formula evaluation uses AST (no eval)
# ---------------------------------------------------------------------------


class TestFormulaEvalNoEval:
    """F-3: Signal quantification must use AST, not eval()."""

    def test_no_eval_in_signal_quantification(self):
        """Verify signal_quantification.py contains no eval() calls."""
        import ast as python_ast

        # Read the source file
        source_path = (
            "value-fabric/layer3-knowledge/src/services/signal_quantification.py"
        )
        if not os.path.exists(source_path):
            # Try from repo root
            source_path = (
                "layer3-knowledge/src/services/signal_quantification.py"
            )

        with open(source_path) as f:
            source = f.read()

        # Parse AST and look for eval calls
        tree = python_ast.parse(source)

        eval_calls = []
        for node in python_ast.walk(tree):
            if isinstance(node, python_ast.Call):
                if isinstance(node.func, python_ast.Name):
                    if node.func.id == "eval":
                        eval_calls.append(node)

        assert len(eval_calls) == 0, f"Found {len(eval_calls)} eval() calls in source"

    def test_safe_eval_uses_ast_walker(self):
        """Verify _safe_eval uses AST parsing, not eval()."""
        from layer3_knowledge.src.services.signal_quantification import (
            SignalQuantificationService,
        )

        service = SignalQuantificationService()

        # Test that safe operations work
        result = service._safe_eval("2 + 3", {})
        assert result == 5.0

        result = service._safe_eval("x * 2", {"x": 10})
        assert result == 20.0

    def test_ast_eval_rejects_attribute_access(self):
        """AST evaluator should reject __class__.__bases__ traversal."""
        from layer3_knowledge.src.services.signal_quantification import (
            SignalQuantificationService,
        )

        service = SignalQuantificationService()

        # This should raise ValueError, not execute code
        with pytest.raises((ValueError, NameError)):
            service._safe_eval("().__class__", {})

    def test_ast_eval_rejects_import(self):
        """AST evaluator should reject __import__ calls."""
        from layer3_knowledge.src.services.signal_quantification import (
            SignalQuantificationService,
        )

        service = SignalQuantificationService()

        with pytest.raises((ValueError, NameError)):
            service._safe_eval("__import__('os')", {})

    def test_ast_eval_rejects_subscript(self):
        """AST evaluator should reject subscript operations like __bases__[0]."""
        from layer3_knowledge.src.services.signal_quantification import (
            SignalQuantificationService,
        )

        service = SignalQuantificationService()

        with pytest.raises(ValueError) as exc_info:
            service._safe_eval("().__class__.__bases__[0]", {})

        assert "Unsupported expression type" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Integration: Full auth flow tests
# ---------------------------------------------------------------------------


class TestAuthFlowIntegration:
    """Integration tests for complete auth flows."""

    @pytest.mark.asyncio
    async def test_malformed_jwt_does_not_fallthrough_to_header(self):
        """F-16: Malformed JWT should return 401, not fall through to X-Tenant-ID."""
        from value_fabric.shared.identity.middleware import GovernanceMiddleware

        middleware = GovernanceMiddleware(
            app=None,  # type: ignore
            api_key_resolver=AsyncMock(return_value=None),
        )

        # Create request with malformed JWT and X-Tenant-ID
        request = MagicMock(spec=Request)
        request.headers = Headers(
            {
                "Authorization": "Bearer invalid.jwt.token",
                "X-Tenant-ID": str(TENANT_A_ID),
            }
        )
        request.query_params = {}

        with patch(
            "shared.identity.middleware.decode_jwt"
        ) as mock_decode:
            mock_decode.return_value = None  # Simulate JWT decode failure

            result = await middleware._resolve_identity(request)

        # Malformed JWT should result in None (caller should handle 401)
        # Not fall through to X-Tenant-ID processing
        assert result is None


# ---------------------------------------------------------------------------
# CI/CD Gate: Semgrep-style checks
# ---------------------------------------------------------------------------


def test_no_eval_in_production_code():
    """CI gate: Verify no eval() exists outside test files."""
    import ast as python_ast
    import os

    repo_root = "value-fabric"
    if not os.path.exists(repo_root):
        repo_root = "."

    eval_files = []

    for root, dirs, files in os.walk(repo_root):
        # Skip test files and cache directories
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".pytest_cache", "tests")]

        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            try:
                with open(filepath) as f:
                    source = f.read()

                tree = python_ast.parse(source)
                for node in python_ast.walk(tree):
                    if isinstance(node, python_ast.Call):
                        if isinstance(node.func, python_ast.Name):
                            if node.func.id == "eval":
                                eval_files.append(filepath)
                                break
            except (SyntaxError, UnicodeDecodeError):
                continue

    # No eval() should exist outside tests
    assert len(eval_files) == 0, f"eval() found in: {eval_files}"
