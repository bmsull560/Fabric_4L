"""FastAPI dependency helpers for identity / authorization.

Import these in route files instead of writing per-endpoint auth logic:

    from shared.identity.dependencies import require_role, require_permission
    from shared.identity.permissions import Role, Permission

    @router.post("/v1/tenants")
    async def create_tenant(ctx = Depends(require_role(Role.SUPER_ADMIN))):
        ...
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from .context import RequestContext, get_request_context
from .permissions import Permission, Role


# ---------------------------------------------------------------------------
# Base dependency
# ---------------------------------------------------------------------------


def get_current_context(request: Request) -> Optional[RequestContext]:
    """Return the current RequestContext or None (public endpoints)."""
    return getattr(request.state, "governance_context", None)


def get_optional_context(request: Request) -> Optional[RequestContext]:
    """Alias for get_current_context; documents optionality at call sites."""
    return get_current_context(request)


def require_authenticated(
    ctx: Optional[RequestContext] = Depends(get_current_context),
) -> RequestContext:
    """Require that the request is authenticated (any identity source).

    Raises HTTP 401 if no identity could be resolved.
    """
    if ctx is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "AUTHENTICATION_REQUIRED",
                "message": "A valid Bearer JWT or X-API-Key is required.",
                "schemes": ["Bearer", "X-API-Key"],
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    return ctx


def require_tenant(
    ctx: RequestContext = Depends(require_authenticated),
) -> UUID:
    """Return the tenant_id from the current context.

    Useful when a handler only needs the tenant_id, not the full context.
    """
    return ctx.tenant_id


# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------


def require_role(*allowed_roles: Role):
    """Dependency factory: require the caller to hold any of *allowed_roles*.

    Usage::

        @router.post("/v1/tenants")
        async def create_tenant(
            ctx = Depends(require_role(Role.SUPER_ADMIN)),
        ):
            ...
    """

    async def _dependency(
        ctx: RequestContext = Depends(require_authenticated),
    ) -> RequestContext:
        if not ctx.has_any_role(*allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "INSUFFICIENT_ROLE",
                    "message": (
                        f"One of the following roles is required: "
                        f"{[r.value for r in allowed_roles]}"
                    ),
                    "required_roles": [r.value for r in allowed_roles],
                    "current_roles": ctx.roles,
                },
            )
        return ctx

    return _dependency


# ---------------------------------------------------------------------------
# Permission-based access control
# ---------------------------------------------------------------------------


def require_permission(permission: Permission):
    """Dependency factory: require a single permission.

    Usage::

        @router.post("/v1/crawl/website")
        async def start_crawl(
            ctx = Depends(require_permission(Permission.WRITE_INGESTION)),
        ):
            ...
    """

    async def _dependency(
        ctx: RequestContext = Depends(require_authenticated),
    ) -> RequestContext:
        if not ctx.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "INSUFFICIENT_PERMISSIONS",
                    "message": f"Permission '{permission.value}' is required.",
                    "required_permission": permission.value,
                    "current_roles": ctx.roles,
                },
            )
        return ctx

    return _dependency


def require_any_permission(*permissions: Permission):
    """Dependency factory: require at least one of the given permissions."""

    async def _dependency(
        ctx: RequestContext = Depends(require_authenticated),
    ) -> RequestContext:
        if not ctx.has_any_permission(*permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "INSUFFICIENT_PERMISSIONS",
                    "message": (
                        f"At least one of the following permissions is required: "
                        f"{[p.value for p in permissions]}"
                    ),
                    "required_permissions": [p.value for p in permissions],
                    "current_roles": ctx.roles,
                },
            )
        return ctx

    return _dependency


def require_all_permissions(*permissions: Permission):
    """Dependency factory: require all of the given permissions."""

    async def _dependency(
        ctx: RequestContext = Depends(require_authenticated),
    ) -> RequestContext:
        missing = [p.value for p in permissions if not ctx.has_permission(p)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "INSUFFICIENT_PERMISSIONS",
                    "message": f"Missing required permissions: {missing}",
                    "required_permissions": [p.value for p in permissions],
                    "missing_permissions": missing,
                    "current_roles": ctx.roles,
                },
            )
        return ctx

    return _dependency


# ---------------------------------------------------------------------------
# Convenience pre-built dependencies
# ---------------------------------------------------------------------------

require_super_admin = require_role(Role.SUPER_ADMIN)
require_tenant_admin = require_role(Role.SUPER_ADMIN, Role.TENANT_ADMIN)
require_content_admin = require_role(
    Role.SUPER_ADMIN, Role.TENANT_ADMIN, Role.CONTENT_ADMIN
)
require_analyst = require_role(
    Role.SUPER_ADMIN, Role.TENANT_ADMIN, Role.CONTENT_ADMIN, Role.ANALYST
)

require_read_search = require_permission(Permission.READ_SEARCH)
require_read_graphrag = require_permission(Permission.READ_GRAPHRAG)
require_write_ingestion = require_permission(Permission.WRITE_INGESTION)
require_write_extraction = require_permission(Permission.WRITE_EXTRACTION)
require_admin_api_keys = require_permission(Permission.ADMIN_API_KEYS)
require_admin_users = require_permission(Permission.ADMIN_USERS)
require_admin_tenants = require_permission(Permission.ADMIN_TENANTS)
