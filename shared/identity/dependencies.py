"""FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Request, status

from .context import RequestContext

logger = logging.getLogger(__name__)


async def get_request_context(request: Request) -> RequestContext:
    """Extract request context from request state.

    This dependency should be used by GovernanceMiddleware
    which sets the context in request.state.context
    """
    context = getattr(request.state, "context", None)
    if context is None:
        return RequestContext()
    return context


async def require_authenticated(
    context: RequestContext = Depends(get_request_context),
) -> RequestContext:
    """Require any valid authentication.

    Raises:
        HTTPException: 401 if no authentication provided
    """
    if not context.tenant_id and not context.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return context


async def require_tenant_context(
    context: RequestContext = Depends(get_request_context),
) -> RequestContext:
    """Require a valid tenant context for RLS enforcement (Task 1.2).

    This dependency ensures that tenant_id is present in the request context,
    which is required for Row-Level Security policies to function correctly.

    Raises:
        HTTPException: 400 if tenant context is missing
    """
    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required. Include X-Tenant-ID header or valid tenant claim.",
        )
    return context


async def require_tenant_admin(
    context: RequestContext = Depends(get_request_context),
) -> RequestContext:
    """Require tenant admin or super admin role.

    Raises:
        HTTPException: 403 if user is not admin
    """
    if not context.is_tenant_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant admin access required",
        )
    return context


async def require_super_admin(
    context: RequestContext = Depends(get_request_context),
) -> RequestContext:
    """Require super admin role.

    Raises:
        HTTPException: 403 if user is not super admin
    """
    if not context.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return context


def require_privileged_access(
    *,
    privilege_reason_header: str = "X-Privileged-Reason",
    require_audit_log: bool = True,
):
    """Factory for privileged access dependency with audit requirements (Task 1.3).

    Super-admin operations that cross tenant boundaries must provide a reason
    in the X-Privileged-Reason header for audit purposes.

    Usage:
        @router.get("/admin/cross-tenant-data")
        async def get_cross_tenant_data(
            context: RequestContext = Depends(
                require_privileged_access(privilege_reason_header="X-Admin-Reason")
            ),
        ):
            ...

    Args:
        privilege_reason_header: Header name containing the access reason
        require_audit_log: If True, requires the reason header to be present

    Returns:
        Dependency function that validates privileged access
    """

    async def _check_privileged(
        request: Request,
        context: RequestContext = Depends(get_request_context),
    ) -> RequestContext:
        # First check if user has super admin role
        if not context.is_super_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Privileged access requires super admin role",
            )

        # Require audit reason if configured
        if require_audit_log:
            reason = request.headers.get(privilege_reason_header)
            if not reason:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Privileged access requires {privilege_reason_header} header with audit reason",
                )
            # Log the privileged access attempt
            logger.warning(
                "Privileged access by super_admin: user=%s tenant=%s reason=%s endpoint=%s",
                context.user_id,
                context.tenant_id,
                reason,
                request.url.path,
            )

        return context

    return _check_privileged


def require_permission(permission: str):
    """Factory for permission-based dependency.

    Usage:
        @router.get("/items")
        async def list_items(
            context: RequestContext = Depends(require_permission("item:read"))
        ):
            ...
    """

    async def _check_permission(
        context: RequestContext = Depends(get_request_context),
    ) -> RequestContext:
        if not context.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return context

    return _check_permission


def require_any_permission(*permissions: str):
    """Factory for requiring any of the specified permissions.

    Usage:
        @router.get("/items")
        async def list_items(
            context: RequestContext = Depends(require_any_permission("item:read", "admin:read"))
        ):
            ...
    """

    async def _check_any_permission(
        context: RequestContext = Depends(get_request_context),
    ) -> RequestContext:
        for permission in permissions:
            if context.has_permission(permission):
                return context
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"One of permissions {list(permissions)} required",
        )

    return _check_any_permission
