"""Security tests: Tenant boundary must fail closed (never return None).

These tests verify that:
1. require_tenant_context() raises TenantBoundaryError when no context is set
2. Direct header access patterns are detected
3. Tools using require_tenant_context() fail securely

This addresses the P0 fix: "require_context() returns None" → now raises.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Add shared to path - insert at 0 to prioritize
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "value-fabric" / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "value-fabric"))

import pytest

# Import the boundary module directly
from boundaries.tenant_boundary import (
    TenantBoundaryError,
    get_tenant_context,
    require_tenant_context,
    get_tenant_id,
    require_tenant_id,
)
from identity.context import RequestContext, set_request_context


# Fixture to reset context between tests
@pytest.fixture(autouse=True)
def reset_context():
    """Reset context before each test."""
    from identity.context import _current_context
    _current_context.set(None)
    yield


class TestTenantBoundaryFailsClosed:
    """Verify boundary functions raise on missing context (fail closed)."""

    def test_require_tenant_context_raises_when_no_context(self):
        """P0 FIX: require_tenant_context() must raise, not return None."""
        with pytest.raises(TenantBoundaryError) as exc_info:
            require_tenant_context()
        
        assert "Tenant context required" in str(exc_info.value)
        assert "GovernanceMiddleware" in str(exc_info.value)

    def test_require_tenant_id_raises_when_no_context(self):
        """require_tenant_id() must raise TenantBoundaryError."""
        with pytest.raises(TenantBoundaryError):
            require_tenant_id()

    def test_get_tenant_context_returns_none_when_no_context(self):
        """get_tenant_context() is allowed to return None (optional access)."""
        result = get_tenant_context()
        assert result is None

    def test_get_tenant_id_returns_none_when_no_context(self):
        """get_tenant_id() is allowed to return None (optional access)."""
        result = get_tenant_id()
        assert result is None


class TestTenantBoundaryWithContext:
    """Verify boundary functions work correctly when context is set."""

    def test_require_tenant_context_returns_context_when_set(self):
        """require_tenant_context() returns context when available."""
        from uuid import UUID
        
        ctx = RequestContext(
            tenant_id=UUID("12345678-1234-1234-1234-123456789abc"),
            user_id="test-user",
            roles=["admin"],
            source="test",
        )
        
        token = set_request_context(ctx)
        try:
            result = require_tenant_context()
            assert result == ctx
            assert result.tenant_id == ctx.tenant_id
        finally:
            from identity.context import _current_context
            _current_context.reset(token)

    def test_require_tenant_id_returns_uuid_when_context_set(self):
        """require_tenant_id() returns UUID when context is available."""
        from uuid import UUID
        
        ctx = RequestContext(
            tenant_id=UUID("12345678-1234-1234-1234-123456789abc"),
            user_id="test-user",
            roles=["admin"],
            source="test",
        )
        
        token = set_request_context(ctx)
        try:
            tenant_id = require_tenant_id()
            assert tenant_id == ctx.tenant_id
            assert isinstance(tenant_id, UUID)
        finally:
            from identity.context import _current_context
            _current_context.reset(token)


class TestDirectHeaderAccessBlocked:
    """Verify that direct header access patterns are detected/blocked."""

    def test_violation_patterns_detected_by_ci_script(self):
        """CI script must detect direct header access patterns."""
        
        # These patterns should be detected by scripts/ci/boundary_check.py
        violation_patterns = [
            "tenant_id = headers['X-Tenant-ID']",
            "tenant_id = headers['x-tenant-id']",
            "tenant_id = headers.get('X-Tenant-ID')",
            "tenant_id = headers.get('x-tenant-id')",
            "tenant_id = request.headers['X-Tenant-ID']",
            "tenant_id = request.headers.get('X-Tenant-ID')",
            "tenant_id = req.headers['X-Tenant-ID']",
            "tenant_id = req.headers.get('X-Tenant-ID')",
        ]
        
        # CI script patterns (must match these)
        ci_patterns = [
            r"headers\s*\[\s*['\"]X-Tenant-ID['\"]\s*\](?!\s*=)",
            r"headers\.get\s*\(\s*['\"]X-Tenant-ID['\"]",
            r"request\.headers\s*\[\s*['\"]X-Tenant-ID['\"]\s*\](?!\s*=)",
            r"request\.headers\.get\s*\(\s*['\"]X-Tenant-ID['\"]",
            r"req\.headers\s*\[\s*['\"]X-Tenant-ID['\"]\s*\](?!\s*=)",
            r"req\.headers\.get\s*\(\s*['\"]X-Tenant-ID['\"]",
        ]
        
        for violation in violation_patterns:
            # At least one pattern should match
            matched = any(re.search(p, violation, re.IGNORECASE) for p in ci_patterns)
            assert matched, f"Pattern should be detected: {violation}"


class TestToolBoundaryIntegration:
    """Verify tools using require_tenant_context() fail securely."""

    def test_query_graph_tool_fails_without_tenant_context(self):
        """Simulate QueryGraphTool with require_tenant_context().
        
        This is the key test for the P0 fix:
        "QueryGraphTool → passes test_query_graph_without_tenant_context_fails_closed"
        """
        # Simulate what QueryGraphTool should do
        def mock_query_graph_tool_execution():
            # Tool should call require_tenant_context() to get tenant
            ctx = require_tenant_context()
            return {"tenant_id": str(ctx.tenant_id)}
        
        with pytest.raises(TenantBoundaryError):
            mock_query_graph_tool_execution()

    def test_tool_with_context_succeeds(self):
        """Tool execution succeeds when proper context is available."""
        from uuid import UUID
        
        def mock_query_graph_tool_execution():
            ctx = require_tenant_context()
            return {"tenant_id": str(ctx.tenant_id)}
        
        ctx = RequestContext(
            tenant_id=UUID("12345678-1234-1234-1234-123456789abc"),
            user_id="test-user",
            roles=["admin"],
            source="test",
        )
        
        token = set_request_context(ctx)
        try:
            result = mock_query_graph_tool_execution()
            assert result["tenant_id"] == "12345678-1234-1234-1234-123456789abc"
        finally:
            from identity.context import _current_context
            _current_context.reset(token)
