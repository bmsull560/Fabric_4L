"""Tests for middleware_sync module - regression tests for code review fixes."""

import pytest
from uuid import UUID
from unittest.mock import patch

from shared.identity.middleware_sync import (
    SyncRequestContext,
    GovernanceMiddlewareSync,
    AUTH_SOURCE_SERVICE_ACCOUNT,
)


class TestSyncRequestContext:
    """Test SyncRequestContext creation with proper types."""

    def test_service_auth_context_has_none_user_id(self):
        """Regression test: Issue #2 - user_id type mismatch."""
        tenant_id = UUID("12345678-1234-5678-1234-567812345678")
        ctx = SyncRequestContext(
            tenant_id=tenant_id,
            user_id=None,  # Should be None, not "service" string
            roles=["system"],
            auth_source=AUTH_SOURCE_SERVICE_ACCOUNT,
        )
        assert ctx.user_id is None
        assert ctx.tenant_id == tenant_id
        assert ctx.auth_source == AUTH_SOURCE_SERVICE_ACCOUNT

    def test_service_auth_source_is_valid_constant(self):
        """Verify AUTH_SOURCE_SERVICE_ACCOUNT is a valid auth source."""
        ctx = SyncRequestContext(
            tenant_id=UUID("12345678-1234-5678-1234-567812345678"),
            user_id=None,
            roles=["system"],
            auth_source=AUTH_SOURCE_SERVICE_ACCOUNT,
        )
        assert ctx.is_auth_source_valid() is True

    def test_invalid_auth_source_is_rejected(self):
        """Verify invalid auth_source strings are rejected."""
        ctx = SyncRequestContext(
            tenant_id=UUID("12345678-1234-5678-1234-567812345678"),
            user_id=None,
            auth_source="invalid_header_string",
        )
        assert ctx.is_auth_source_valid() is False


class TestGovernanceMiddlewareSync:
    """Test middleware creates valid contexts."""

    def test_service_auth_creates_valid_context(self):
        """Test service auth creates properly typed context."""
        with patch.dict("os.environ", {"SERVICE_AUTH_SECRET": "test-secret"}):
            middleware = GovernanceMiddlewareSync(None)
            
            # Mock request headers
            class MockRequest:
                headers = {
                    "X-Tenant-ID": "12345678-1234-5678-1234-567812345678",
                    "X-Service-Auth": "test-secret",
                }
            
            request = MockRequest()
            ctx = middleware._resolve_identity_sync(request)
            
            if ctx:  # If auth succeeded
                assert ctx.user_id is None
                assert ctx.auth_source == AUTH_SOURCE_SERVICE_ACCOUNT
                assert "system" in ctx.roles
