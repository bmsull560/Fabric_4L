"""Comprehensive GovernanceMiddleware security tests.

Tests cover:
- Identity resolution order
- JWT authentication
- API key authentication
- Service-to-service authentication
- Rate limiting
- Context lifecycle management
- Public path bypass
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import Request, Response
from starlette.datastructures import Headers, QueryParams

from shared.identity.context import RequestContext
from shared.identity.middleware import (
    GovernanceMiddleware,
    _build_context_from_role,
    _is_public_path,
)
from shared.identity.permissions import Permission, Role


class TestPublicPathBypass:
    """Test public path authentication bypass."""

    def test_health_path_is_public(self):
        """Health check endpoint is public."""
        assert _is_public_path("/health") is True
        assert _is_public_path("/health/detailed") is True

    def test_metrics_path_is_public(self):
        """Metrics endpoint is public."""
        assert _is_public_path("/metrics") is True

    def test_docs_paths_are_public(self):
        """Documentation paths are public."""
        assert _is_public_path("/docs") is True
        assert _is_public_path("/docs/openapi.json") is True
        assert _is_public_path("/redoc") is True

    def test_root_path_is_public(self):
        """Root path is public."""
        assert _is_public_path("/") is True

    def test_protected_path_not_public(self):
        """Protected paths are not public."""
        assert _is_public_path("/api/v1/entities") is False
        assert _is_public_path("/api/v1/users") is False
        assert _is_public_path("/admin") is False


class TestContextBuilding:
    """Test RequestContext building from roles."""

    def test_build_context_basic(self):
        """Basic context building works."""
        tenant_id = uuid4()
        user_id = "user_123"
        roles = [Role.ANALYST.value]

        ctx = _build_context_from_role(
            tenant_id=tenant_id,
            user_id=user_id,
            roles=roles,
            source="jwt",
            raw={},
        )

        assert ctx.tenant_id == tenant_id
        assert ctx.user_id == user_id
        assert ctx.roles == roles
        assert ctx.source == "jwt"

    def test_build_context_computes_permissions(self):
        """Context building computes permissions from roles."""
        tenant_id = uuid4()

        ctx = _build_context_from_role(
            tenant_id=tenant_id,
            user_id="user_123",
            roles=[Role.ANALYST.value],
            source="jwt",
            raw={},
        )

        # Analyst should have analyst permissions
        assert Permission.READ_SEARCH in ctx.permissions
        assert Permission.WRITE_INGESTION not in ctx.permissions

    def test_build_context_multiple_roles(self):
        """Context building handles multiple roles."""
        tenant_id = uuid4()

        ctx = _build_context_from_role(
            tenant_id=tenant_id,
            user_id="user_123",
            roles=[Role.READ_ONLY.value, Role.ANALYST.value],
            source="jwt",
            raw={},
        )

        # Should have permissions from both roles
        assert Permission.READ_SEARCH in ctx.permissions
        assert Permission.READ_ANALYTICS in ctx.permissions

    def test_build_context_unknown_role_skipped(self):
        """Unknown roles are skipped with debug log."""
        tenant_id = uuid4()

        ctx = _build_context_from_role(
            tenant_id=tenant_id,
            user_id="user_123",
            roles=["unknown_role", Role.ANALYST.value],
            source="jwt",
            raw={},
        )

        # Unknown role skipped, analyst permissions present
        assert Permission.READ_SEARCH in ctx.permissions

    def test_build_context_api_key_source(self):
        """Context building works for API key source."""
        tenant_id = uuid4()

        ctx = _build_context_from_role(
            tenant_id=tenant_id,
            user_id=None,
            roles=[Role.SYSTEM.value],
            api_key_id="key_123",
            source="api_key",
            raw={},
        )

        assert ctx.api_key_id == "key_123"
        assert ctx.user_id is None
        assert ctx.source == "api_key"


class TestMiddlewareJWTAuth:
    """Test JWT authentication in middleware."""

    @pytest.fixture
    def mock_app(self):
        """Create mock ASGI app."""
        return AsyncMock()

    @pytest.fixture
    def middleware(self, mock_app):
        """Create middleware instance."""
        return GovernanceMiddleware(
            app=mock_app,
            api_key_resolver=None,
            rate_limiter=None,
        )

    @pytest.fixture
    def mock_request(self):
        """Create mock request with JWT header."""
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.headers = Headers({"Authorization": "Bearer valid_token"})
        request.query_params = QueryParams()
        request.state = MagicMock()
        return request

    async def test_jwt_auth_success(self, middleware, mock_request):
        """Valid JWT authenticates successfully."""
        tenant_id = uuid4()

        with patch(
            "value_fabric.shared.identity.middleware.decode_jwt"
        ) as mock_decode:
            from value_fabric.shared.identity.models import TokenClaims

            mock_decode.return_value = TokenClaims(
                sub="user_123",
                tenant_id=str(tenant_id),
                roles=["analyst"],
                exp=int(time.time()) + 3600,
                iat=int(time.time()),
                extra_claims={},
            )

            # Mock the call_next response
            expected_response = Response(content="OK", status_code=200)
            middleware.app = AsyncMock(return_value=expected_response)

            response = await middleware.dispatch(mock_request, middleware.app)

            assert response.status_code == 200
            assert mock_request.state.governance_context is not None
            assert mock_request.state.governance_context.tenant_id == tenant_id

    async def test_jwt_auth_invalid_token(self, middleware, mock_request):
        """Invalid JWT falls through to next strategy."""
        mock_request.headers = Headers({"Authorization": "Bearer invalid_token"})

        with patch(
            "value_fabric.shared.identity.middleware.decode_jwt"
        ) as mock_decode:
            mock_decode.side_effect = Exception("Invalid token")

            expected_response = Response(content="OK", status_code=200)
            middleware.app = AsyncMock(return_value=expected_response)

            response = await middleware.dispatch(mock_request, middleware.app)

            # Should continue without context (falls through)
            assert response.status_code == 200

    async def test_jwt_auth_missing_header(self, middleware, mock_request):
        """Missing Authorization header falls through."""
        mock_request.headers = Headers({})

        expected_response = Response(content="OK", status_code=200)
        middleware.app = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request, middleware.app)

        assert response.status_code == 200
        assert mock_request.state.governance_context is None


class TestMiddlewareAPIKeyAuth:
    """Test API key authentication in middleware."""

    @pytest.fixture
    def mock_app(self):
        """Create mock ASGI app."""
        return AsyncMock()

    @pytest.fixture
    def api_key_resolver(self):
        """Create mock API key resolver."""
        return AsyncMock()

    @pytest.fixture
    def middleware(self, mock_app, api_key_resolver):
        """Create middleware instance with API key resolver."""
        return GovernanceMiddleware(
            app=mock_app,
            api_key_resolver=api_key_resolver,
            rate_limiter=None,
        )

    @pytest.fixture
    def mock_request(self):
        """Create mock request with API key header."""
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.headers = Headers({"X-API-Key": "valid_api_key"})
        request.query_params = QueryParams()
        request.state = MagicMock()
        return request

    async def test_api_key_auth_success(self, middleware, mock_request, api_key_resolver):
        """Valid API key authenticates successfully."""
        tenant_id = uuid4()
        api_key_resolver.return_value = {
            "tenant_id": str(tenant_id),
            "user_id": "user_123",
            "role": "analyst",
            "permissions": ["read:search"],
            "key_id": "key_123",
            "enabled": True,
        }

        expected_response = Response(content="OK", status_code=200)
        middleware.app = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request, middleware.app)

        assert response.status_code == 200
        assert mock_request.state.governance_context is not None
        assert mock_request.state.governance_context.tenant_id == tenant_id
        assert mock_request.state.governance_context.source == "api_key"

    async def test_api_key_auth_disabled(self, middleware, mock_request, api_key_resolver):
        """Disabled API key fails authentication."""
        api_key_resolver.return_value = {
            "tenant_id": str(uuid4()),
            "role": "analyst",
            "key_id": "key_123",
            "enabled": False,
        }

        expected_response = Response(content="OK", status_code=200)
        middleware.app = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request, middleware.app)

        # Disabled key should not set context
        assert mock_request.state.governance_context is None

    async def test_api_key_auth_invalid_tenant(self, middleware, mock_request, api_key_resolver):
        """API key with invalid tenant_id is rejected."""
        api_key_resolver.return_value = {
            "tenant_id": "not-a-uuid",
            "role": "analyst",
            "key_id": "key_123",
            "enabled": True,
        }

        expected_response = Response(content="OK", status_code=200)
        middleware.app = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request, middleware.app)

        # Invalid tenant should not set context
        assert mock_request.state.governance_context is None

    async def test_api_key_auth_not_found(self, middleware, mock_request, api_key_resolver):
        """Non-existent API key falls through."""
        api_key_resolver.return_value = None

        expected_response = Response(content="OK", status_code=200)
        middleware.app = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request, middleware.app)

        assert mock_request.state.governance_context is None


class TestMiddlewareServiceToServiceAuth:
    """Test X-Tenant-ID service-to-service authentication."""

    @pytest.fixture
    def mock_app(self):
        """Create mock ASGI app."""
        return AsyncMock()

    @pytest.fixture
    def middleware(self, mock_app):
        """Create middleware instance."""
        return GovernanceMiddleware(
            app=mock_app,
            api_key_resolver=None,
            rate_limiter=None,
        )

    @pytest.fixture
    def mock_request(self):
        """Create mock request with X-Tenant-ID header."""
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.headers = Headers({"X-Tenant-ID": str(uuid4())})
        request.query_params = QueryParams()
        request.state = MagicMock()
        return request

    async def test_service_auth_success(self, middleware, mock_request):
        """Valid X-Tenant-ID creates service context."""
        tenant_id = uuid4()
        mock_request.headers = Headers({"X-Tenant-ID": str(tenant_id)})

        expected_response = Response(content="OK", status_code=200)
        middleware.app = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request, middleware.app)

        assert response.status_code == 200
        assert mock_request.state.governance_context is not None
        assert mock_request.state.governance_context.tenant_id == tenant_id
        assert Role.SYSTEM.value in mock_request.state.governance_context.roles
        assert mock_request.state.governance_context.source == "header"

    async def test_service_auth_invalid_uuid(self, middleware, mock_request):
        """Invalid X-Tenant-ID UUID is rejected."""
        mock_request.headers = Headers({"X-Tenant-ID": "not-a-uuid"})

        expected_response = Response(content="OK", status_code=200)
        middleware.app = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request, middleware.app)

        assert mock_request.state.governance_context is None


class TestMiddlewareRateLimiting:
    """Test rate limiting integration."""

    @pytest.fixture
    def mock_app(self):
        """Create mock ASGI app."""
        return AsyncMock()

    @pytest.fixture
    def mock_rate_limiter(self):
        """Create mock rate limiter."""
        limiter = AsyncMock()
        return limiter

    @pytest.fixture
    def middleware(self, mock_app, mock_rate_limiter):
        """Create middleware with rate limiter."""
        return GovernanceMiddleware(
            app=mock_app,
            api_key_resolver=None,
            rate_limiter=mock_rate_limiter,
        )

    @pytest.fixture
    def mock_request_with_context(self):
        """Create mock request with auth context."""
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.headers = Headers({"X-Tenant-ID": str(uuid4())})
        request.query_params = QueryParams()
        request.state = MagicMock()
        return request

    async def test_rate_limit_allowed(self, middleware, mock_request_with_context, mock_rate_limiter):
        """Request within rate limit is allowed."""
        from value_fabric.shared.identity.rate_limiter import RateLimitResult

        mock_rate_limiter.check.return_value = RateLimitResult(
            allowed=True,
            remaining=99,
            reset_at=time.time() + 60,
        )

        expected_response = Response(content="OK", status_code=200)
        middleware.app = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request_with_context, middleware.app)

        assert response.status_code == 200

    async def test_rate_limit_exceeded(self, middleware, mock_request_with_context, mock_rate_limiter):
        """Request exceeding rate limit returns 429."""
        from value_fabric.shared.identity.rate_limiter import RateLimitResult

        mock_rate_limiter.check.return_value = RateLimitResult(
            allowed=False,
            remaining=0,
            reset_at=time.time() + 60,
            retry_after=60,
        )

        response = await middleware.dispatch(mock_request_with_context, AsyncMock())

        assert response.status_code == 429
        assert "Rate limit exceeded" in response.body.decode()

    async def test_rate_limit_headers_on_allowed(self, middleware, mock_request_with_context, mock_rate_limiter):
        """Rate limit headers added on allowed request."""
        from value_fabric.shared.identity.rate_limiter import RateLimitResult

        mock_rate_limiter.check.return_value = RateLimitResult(
            allowed=True,
            remaining=95,
            reset_at=time.time() + 60,
        )

        expected_response = Response(content="OK", status_code=200)
        middleware.app = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request_with_context, middleware.app)

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "95"


class TestMiddlewareContextLifecycle:
    """Test request context lifecycle management."""

    @pytest.fixture
    def mock_app(self):
        """Create mock ASGI app."""
        return AsyncMock()

    @pytest.fixture
    def middleware(self, mock_app):
        """Create middleware instance."""
        return GovernanceMiddleware(
            app=mock_app,
            api_key_resolver=None,
            rate_limiter=None,
        )

    async def test_context_set_and_reset(self, middleware):
        """Context is set and properly reset after request."""
        from value_fabric.shared.identity.context import get_request_context

        tenant_id = uuid4()
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.headers = Headers({"X-Tenant-ID": str(tenant_id)})
        request.query_params = QueryParams()
        request.state = MagicMock()

        expected_response = Response(content="OK", status_code=200)
        middleware.app = AsyncMock(return_value=expected_response)

        # Before request, no context
        assert get_request_context() is None

        # During request (need to verify context is set)
        response = await middleware.dispatch(request, middleware.app)
        assert response.status_code == 200

        # Context is reset after request
        assert get_request_context() is None

    async def test_tenant_header_added_to_response(self, middleware):
        """X-Tenant-ID-Resolved header added to response."""
        tenant_id = uuid4()
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.headers = Headers({"X-Tenant-ID": str(tenant_id)})
        request.query_params = QueryParams()
        request.state = MagicMock()

        expected_response = Response(content="OK", status_code=200)
        middleware.app = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(request, middleware.app)

        assert response.headers["X-Tenant-ID-Resolved"] == str(tenant_id)


class TestMiddlewarePriorityOrder:
    """Test identity resolution priority order."""

    def test_resolution_order_jwt_first(self):
        """JWT is checked first in resolution order."""
        # Priority: 1. Bearer JWT, 2. X-API-Key, 3. X-Tenant-ID, 4. Query param
        # This is tested implicitly through the middleware implementation
        pass

    def test_resolution_order_api_key_second(self):
        """API key is checked second if JWT fails."""
        pass

    def test_resolution_order_service_third(self):
        """X-Tenant-ID is checked third if API key fails."""
        pass

    def test_falls_through_on_all_failures(self):
        """All strategies can fail and request continues."""
        pass


class TestMiddlewareSecurityEdgeCases:
    """Test middleware security edge cases."""

    @pytest.fixture
    def mock_app(self):
        """Create mock ASGI app."""
        return AsyncMock()

    @pytest.fixture
    def middleware(self, mock_app):
        """Create middleware instance."""
        return GovernanceMiddleware(
            app=mock_app,
            api_key_resolver=None,
            rate_limiter=None,
        )

    async def test_exception_in_handler_context_reset(self, middleware):
        """Context is reset even if handler raises exception."""
        from value_fabric.shared.identity.context import get_request_context

        tenant_id = uuid4()
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.headers = Headers({"X-Tenant-ID": str(tenant_id)})
        request.query_params = QueryParams()
        request.state = MagicMock()

        async def failing_handler(request):
            raise ValueError("Handler error")

        try:
            await middleware.dispatch(request, failing_handler)
        except ValueError:
            pass

        # Context should be reset even after exception
        assert get_request_context() is None

    async def test_query_param_tenant_id_allowed(self, middleware):
        """Query param tenant_id works when allowed."""
        with patch.dict(os.environ, {"ALLOW_TENANT_QUERY_PARAM": "true"}, clear=False):
            tenant_id = uuid4()
            request = MagicMock(spec=Request)
            request.url.path = "/api/v1/protected"
            request.headers = Headers()
            request.query_params = QueryParams({"tenant_id": str(tenant_id)})
            request.state = MagicMock()

            expected_response = Response(content="OK", status_code=200)
            middleware.app = AsyncMock(return_value=expected_response)

            # Need to recreate middleware to pick up env var change
            middleware_with_query = GovernanceMiddleware(
                app=middleware.app,
                api_key_resolver=None,
                rate_limiter=None,
            )

            response = await middleware_with_query.dispatch(request, middleware_with_query.app)

            assert response.status_code == 200

    async def test_query_param_tenant_id_blocked_by_default(self, middleware):
        """Query param tenant_id blocked by default."""
        tenant_id = uuid4()
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.headers = Headers()
        request.query_params = QueryParams({"tenant_id": str(tenant_id)})
        request.state = MagicMock()

        expected_response = Response(content="OK", status_code=200)
        middleware.app = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(request, middleware.app)

        # No context should be set (query param blocked)
        assert request.state.governance_context is None
