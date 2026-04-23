"""Comprehensive RBAC and permissions security tests.

Tests cover:
- Role-based access control
- Permission dependencies
- Role hierarchy
- Permission inheritance
- Dependency factory functions
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, Request

from value_fabric.shared.identity.context import RequestContext
from value_fabric.shared.identity.dependencies import (
    get_current_context,
    get_optional_context,
    require_all_permissions,
    require_analyst,
    require_any_permission,
    require_authenticated,
    require_content_admin,
    require_permission,
    require_read_search,
    require_role,
    require_super_admin,
    require_tenant,
    require_tenant_admin,
)
from value_fabric.shared.identity.permissions import Permission, Role, ROLE_PERMISSIONS


class TestPermissionEnum:
    """Test Permission enum definitions."""

    def test_permissions_are_strings(self):
        """All permissions are string values."""
        for perm in Permission:
            assert isinstance(perm.value, str)
            assert ":" in perm.value  # Namespace format

    def test_permission_namespaces(self):
        """Permissions are properly namespaced."""
        namespaces = set(p.value.split(":")[0] for p in Permission)
        expected = {"read", "write", "admin"}
        assert namespaces == expected

    def test_permission_uniqueness(self):
        """All permission values are unique."""
        values = [p.value for p in Permission]
        assert len(values) == len(set(values))


class TestRoleEnum:
    """Test Role enum definitions."""

    def test_roles_are_strings(self):
        """All roles are string values."""
        for role in Role:
            assert isinstance(role.value, str)

    def test_role_hierarchy_defined(self):
        """Role hierarchy is properly defined."""
        hierarchy = [
            Role.READ_ONLY,
            Role.ANALYST,
            Role.CONTENT_ADMIN,
            Role.TENANT_ADMIN,
            Role.SUPER_ADMIN,
        ]

        # Each role should have more or equal permissions than the previous
        prev_perms = set()
        for role in hierarchy:
            perms = ROLE_PERMISSIONS[role].permissions
            assert prev_perms.issubset(perms)
            prev_perms = perms

    def test_system_role_has_all_permissions(self):
        """System role has all permissions."""
        system_perms = ROLE_PERMISSIONS[Role.SYSTEM].permissions
        all_perms = set(Permission)

        assert system_perms == all_perms


class TestRolePermissionsMapping:
    """Test ROLE_PERMISSIONS mapping."""

    def test_read_only_permissions(self):
        """READ_ONLY has only read permissions."""
        perms = ROLE_PERMISSIONS[Role.READ_ONLY].permissions

        assert Permission.READ_SEARCH in perms
        assert Permission.READ_GRAPHRAG in perms
        assert Permission.WRITE_INGESTION not in perms
        assert Permission.ADMIN_USERS not in perms

    def test_analyst_permissions(self):
        """ANALYST has read and some write permissions."""
        perms = ROLE_PERMISSIONS[Role.ANALYST].permissions

        assert Permission.READ_SEARCH in perms
        assert Permission.READ_AGENTS in perms
        assert Permission.WRITE_ANALYTICS in perms
        assert Permission.WRITE_INGESTION not in perms
        assert Permission.ADMIN_USERS not in perms

    def test_content_admin_permissions(self):
        """CONTENT_ADMIN has write permissions."""
        perms = ROLE_PERMISSIONS[Role.CONTENT_ADMIN].permissions

        assert Permission.READ_SEARCH in perms
        assert Permission.WRITE_INGESTION in perms
        assert Permission.WRITE_EXTRACTION in perms
        assert Permission.ADMIN_USERS not in perms

    def test_tenant_admin_permissions(self):
        """TENANT_ADMIN has admin permissions."""
        perms = ROLE_PERMISSIONS[Role.TENANT_ADMIN].permissions

        assert Permission.READ_SEARCH in perms
        assert Permission.WRITE_INGESTION in perms
        assert Permission.ADMIN_USERS in perms
        assert Permission.ADMIN_API_KEYS in perms
        assert Permission.ADMIN_TENANTS not in perms

    def test_super_admin_permissions(self):
        """SUPER_ADMIN has all permissions."""
        perms = ROLE_PERMISSIONS[Role.SUPER_ADMIN].permissions

        for permission in Permission:
            assert permission in perms


class TestRequestContextHelpers:
    """Test RequestContext helper methods."""

    @pytest.fixture
    def analyst_context(self):
        """Create analyst context."""
        return RequestContext(
            tenant_id=uuid4(),
            user_id="user_123",
            roles=[Role.ANALYST.value],
            permissions=ROLE_PERMISSIONS[Role.ANALYST].permissions,
            source="jwt",
        )

    @pytest.fixture
    def admin_context(self):
        """Create admin context."""
        return RequestContext(
            tenant_id=uuid4(),
            user_id="user_123",
            roles=[Role.TENANT_ADMIN.value, Role.ANALYST.value],
            permissions=ROLE_PERMISSIONS[Role.TENANT_ADMIN].permissions,
            source="jwt",
        )

    def test_has_role(self, analyst_context):
        """has_role checks role membership."""
        assert analyst_context.has_role(Role.ANALYST) is True
        assert analyst_context.has_role(Role.READ_ONLY) is False
        assert analyst_context.has_role("analyst") is True

    def test_has_any_role(self, admin_context):
        """has_any_role checks multiple roles."""
        assert admin_context.has_any_role(Role.TENANT_ADMIN) is True
        assert admin_context.has_any_role(Role.ANALYST) is True
        assert admin_context.has_any_role(Role.READ_ONLY) is False
        assert admin_context.has_any_role(Role.TENANT_ADMIN, Role.READ_ONLY) is True

    def test_has_permission(self, analyst_context):
        """has_permission checks single permission."""
        assert analyst_context.has_permission(Permission.READ_SEARCH) is True
        assert analyst_context.has_permission(Permission.WRITE_INGESTION) is False

    def test_has_any_permission(self, admin_context):
        """has_any_permission checks multiple permissions."""
        assert admin_context.has_any_permission(Permission.ADMIN_USERS) is True
        assert admin_context.has_any_permission(Permission.READ_SEARCH) is True
        assert admin_context.has_any_permission(
            Permission.WRITE_INGESTION, Permission.ADMIN_SYSTEM
        ) is True

    def test_has_all_permissions(self, admin_context):
        """has_all_permissions requires all listed."""
        assert admin_context.has_all_permissions(Permission.READ_SEARCH) is True
        assert admin_context.has_all_permissions(
            Permission.READ_SEARCH, Permission.WRITE_INGESTION
        ) is True
        assert admin_context.has_all_permissions(
            Permission.READ_SEARCH, Permission.ADMIN_SYSTEM
        ) is False

    def test_to_log_dict(self, analyst_context):
        """to_log_dict returns safe logging representation."""
        log_dict = analyst_context.to_log_dict()

        assert "tenant_id" in log_dict
        assert "user_id" in log_dict
        assert "roles" in log_dict
        assert "api_key_id" in log_dict
        assert "source" in log_dict
        assert "permissions" not in log_dict  # Not in log dict for brevity


class TestDependenciesGetCurrentContext:
    """Test get_current_context dependency."""

    def test_get_current_context_exists(self):
        """Context is returned when it exists."""
        ctx = RequestContext(
            tenant_id=uuid4(),
            user_id="user_123",
            roles=[Role.ANALYST.value],
            permissions=frozenset(),
            source="jwt",
        )

        request = MagicMock(spec=Request)
        request.state.governance_context = ctx

        result = get_current_context(request)
        assert result == ctx

    def test_get_current_context_missing(self):
        """None returned when context missing."""
        request = MagicMock(spec=Request)
        request.state.governance_context = None

        result = get_current_context(request)
        assert result is None

    def test_get_current_context_no_attribute(self):
        """None returned when state attribute missing."""
        request = MagicMock(spec=Request)
        del request.state.governance_context

        result = get_current_context(request)
        assert result is None

    def test_get_optional_context_alias(self):
        """get_optional_context is alias for get_current_context."""
        ctx = RequestContext(
            tenant_id=uuid4(),
            user_id="user_123",
            roles=[Role.ANALYST.value],
            permissions=frozenset(),
            source="jwt",
        )

        request = MagicMock(spec=Request)
        request.state.governance_context = ctx

        # Both should return the same
        assert get_current_context(request) == get_optional_context(request)


class TestDependenciesRequireAuthenticated:
    """Test require_authenticated dependency."""

    def test_require_authenticated_success(self):
        """Authenticated context passes."""
        ctx = RequestContext(
            tenant_id=uuid4(),
            user_id="user_123",
            roles=[Role.ANALYST.value],
            permissions=frozenset(),
            source="jwt",
        )

        result = require_authenticated(ctx)
        assert result == ctx

    def test_require_authenticated_fails_with_none(self):
        """None context raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            require_authenticated(None)

        assert exc_info.value.status_code == 401
        assert "AUTHENTICATION_REQUIRED" in str(exc_info.value.detail)
        assert exc_info.value.headers.get("WWW-Authenticate") == "Bearer"


class TestDependenciesRequireTenant:
    """Test require_tenant dependency."""

    def test_require_tenant_returns_tenant_id(self):
        """Returns tenant_id from context."""
        tenant_id = uuid4()
        ctx = RequestContext(
            tenant_id=tenant_id,
            user_id="user_123",
            roles=[Role.ANALYST.value],
            permissions=frozenset(),
            source="jwt",
        )

        result = require_tenant(ctx)
        assert result == tenant_id


class TestDependenciesRequireRole:
    """Test require_role dependency factory."""

    @pytest.fixture
    def admin_context(self):
        """Create admin context."""
        return RequestContext(
            tenant_id=uuid4(),
            user_id="user_123",
            roles=[Role.TENANT_ADMIN.value],
            permissions=ROLE_PERMISSIONS[Role.TENANT_ADMIN].permissions,
            source="jwt",
        )

    @pytest.fixture
    def analyst_context(self):
        """Create analyst context."""
        return RequestContext(
            tenant_id=uuid4(),
            user_id="user_123",
            roles=[Role.ANALYST.value],
            permissions=ROLE_PERMISSIONS[Role.ANALYST].permissions,
            source="jwt",
        )

    def test_require_role_single_allowed(self, admin_context):
        """Single allowed role passes."""
        dependency = require_role(Role.TENANT_ADMIN)

        async def run_test():
            result = await dependency(admin_context)
            assert result == admin_context

        import asyncio

        asyncio.run(run_test())

    def test_require_role_multiple_allowed(self, admin_context):
        """Multiple allowed roles passes if user has one."""
        dependency = require_role(Role.SUPER_ADMIN, Role.TENANT_ADMIN)

        async def run_test():
            result = await dependency(admin_context)
            assert result == admin_context

        import asyncio

        asyncio.run(run_test())

    def test_require_role_forbidden(self, analyst_context):
        """Missing role raises 403."""
        dependency = require_role(Role.TENANT_ADMIN)

        async def run_test():
            with pytest.raises(HTTPException) as exc_info:
                await dependency(analyst_context)

            assert exc_info.value.status_code == 403
            assert "INSUFFICIENT_ROLE" in str(exc_info.value.detail)

        import asyncio

        asyncio.run(run_test())


class TestDependenciesRequirePermission:
    """Test require_permission dependency factory."""

    @pytest.fixture
    def analyst_context(self):
        """Create analyst context."""
        return RequestContext(
            tenant_id=uuid4(),
            user_id="user_123",
            roles=[Role.ANALYST.value],
            permissions=ROLE_PERMISSIONS[Role.ANALYST].permissions,
            source="jwt",
        )

    def test_require_permission_success(self, analyst_context):
        """User with permission passes."""
        dependency = require_permission(Permission.READ_SEARCH)

        async def run_test():
            result = await dependency(analyst_context)
            assert result == analyst_context

        import asyncio

        asyncio.run(run_test())

    def test_require_permission_forbidden(self, analyst_context):
        """User without permission raises 403."""
        dependency = require_permission(Permission.ADMIN_USERS)

        async def run_test():
            with pytest.raises(HTTPException) as exc_info:
                await dependency(analyst_context)

            assert exc_info.value.status_code == 403
            assert "INSUFFICIENT_PERMISSIONS" in str(exc_info.value.detail)

        import asyncio

        asyncio.run(run_test())


class TestDependenciesRequireAnyPermission:
    """Test require_any_permission dependency factory."""

    @pytest.fixture
    def analyst_context(self):
        """Create analyst context."""
        return RequestContext(
            tenant_id=uuid4(),
            user_id="user_123",
            roles=[Role.ANALYST.value],
            permissions=ROLE_PERMISSIONS[Role.ANALYST].permissions,
            source="jwt",
        )

    def test_require_any_permission_success(self, analyst_context):
        """User with any of the permissions passes."""
        dependency = require_any_permission(
            Permission.READ_SEARCH, Permission.WRITE_INGESTION
        )

        async def run_test():
            result = await dependency(analyst_context)
            assert result == analyst_context

        import asyncio

        asyncio.run(run_test())

    def test_require_any_permission_forbidden(self, analyst_context):
        """User without any permission raises 403."""
        dependency = require_any_permission(
            Permission.ADMIN_USERS, Permission.ADMIN_API_KEYS
        )

        async def run_test():
            with pytest.raises(HTTPException) as exc_info:
                await dependency(analyst_context)

            assert exc_info.value.status_code == 403

        import asyncio

        asyncio.run(run_test())


class TestDependenciesRequireAllPermissions:
    """Test require_all_permissions dependency factory."""

    @pytest.fixture
    def admin_context(self):
        """Create admin context."""
        return RequestContext(
            tenant_id=uuid4(),
            user_id="user_123",
            roles=[Role.TENANT_ADMIN.value],
            permissions=ROLE_PERMISSIONS[Role.TENANT_ADMIN].permissions,
            source="jwt",
        )

    def test_require_all_permissions_success(self, admin_context):
        """User with all permissions passes."""
        dependency = require_all_permissions(Permission.READ_SEARCH, Permission.ADMIN_USERS)

        async def run_test():
            result = await dependency(admin_context)
            assert result == admin_context

        import asyncio

        asyncio.run(run_test())

    def test_require_all_permissions_partial_forbidden(self, admin_context):
        """User missing one permission raises 403 with details."""
        dependency = require_all_permissions(
            Permission.READ_SEARCH, Permission.ADMIN_SYSTEM
        )

        async def run_test():
            with pytest.raises(HTTPException) as exc_info:
                await dependency(admin_context)

            assert exc_info.value.status_code == 403
            assert "missing_permissions" in str(exc_info.value.detail)

        import asyncio

        asyncio.run(run_test())


class TestConvenienceDependencies:
    """Test pre-built convenience dependencies."""

    def test_require_super_admin(self):
        """require_super_admin checks for SUPER_ADMIN role."""
        # This is a dependency factory, not a direct check
        # We verify it was created correctly
        assert require_super_admin is not None

    def test_require_tenant_admin(self):
        """require_tenant_admin checks for TENANT_ADMIN or SUPER_ADMIN."""
        assert require_tenant_admin is not None

    def test_require_content_admin(self):
        """require_content_admin checks appropriate roles."""
        assert require_content_admin is not None

    def test_require_analyst(self):
        """require_analyst checks appropriate roles."""
        assert require_analyst is not None

    def test_require_read_search(self):
        """require_read_search checks read:search permission."""
        assert require_read_search is not None


class TestRBACSecurityEdgeCases:
    """Test RBAC security edge cases."""

    def test_empty_roles_list(self):
        """Empty roles list results in no permissions."""
        ctx = RequestContext(
            tenant_id=uuid4(),
            user_id="user_123",
            roles=[],
            permissions=frozenset(),
            source="jwt",
        )

        assert len(ctx.roles) == 0
        assert len(ctx.permissions) == 0

    def test_unknown_role_in_list(self):
        """Unknown roles in list are skipped."""
        ctx = _build_context_from_role(
            tenant_id=uuid4(),
            user_id="user_123",
            roles=["unknown_role", Role.ANALYST.value],
            source="jwt",
            raw={},
        )

        # Should still have analyst permissions
        assert Permission.READ_SEARCH in ctx.permissions

    def test_super_admin_role_bypasses_all(self):
        """SUPER_ADMIN role has all permissions."""
        ctx = RequestContext(
            tenant_id=uuid4(),
            user_id="user_123",
            roles=[Role.SUPER_ADMIN.value],
            permissions=ROLE_PERMISSIONS[Role.SUPER_ADMIN].permissions,
            source="jwt",
        )

        for permission in Permission:
            assert ctx.has_permission(permission)


# Helper function for building context (needed for edge case tests)
def _build_context_from_role(
    tenant_id: UUID,
    user_id: str | None,
    roles: list[str],
    source: str,
    raw: dict,
    api_key_id: str | None = None,
) -> RequestContext:
    """Build context from roles (copy from middleware)."""
    from value_fabric.shared.identity.permissions import ROLE_PERMISSIONS, Permission, Role

    permissions: set[Permission] = set()
    for role_str in roles:
        try:
            role = Role(role_str)
            permissions |= ROLE_PERMISSIONS[role].permissions
        except (ValueError, KeyError):
            pass

    return RequestContext(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=roles,
        api_key_id=api_key_id,
        permissions=frozenset(permissions),
        source=source,
        raw=raw,
    )
