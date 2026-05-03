"""FastAPI dependency helpers for identity / authorization.

Import these in route files instead of writing per-endpoint auth logic:

    from value_fabric.shared.identity.dependencies import require_role, require_permission
    from value_fabric.shared.identity.permissions import Role, Permission

    @router.post("/v1/tenants")
    async def create_tenant(ctx = Depends(require_role(Role.SUPER_ADMIN))):
        ...
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from .context import RequestContext
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


def require_tenant_context(
    ctx: Optional[RequestContext] = Depends(get_current_context),
) -> RequestContext:
    """Require that tenant context is present in the request.

    Raises HTTP 400 if tenant_id is missing in RequestContext.

    This is different from require_tenant which returns the tenant_id UUID.
    This function returns the full RequestContext after validating tenant_id is present.
    """
    if ctx is None or not ctx.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required. Ensure request has passed through GovernanceMiddleware.",
        )
    return ctx


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
require_admin = require_role(Role.SUPER_ADMIN, Role.TENANT_ADMIN, Role.CONTENT_ADMIN)

require_read_search = require_permission(Permission.READ_SEARCH)
require_read_graphrag = require_permission(Permission.READ_GRAPHRAG)
require_write_ingestion = require_permission(Permission.WRITE_INGESTION)
require_write_extraction = require_permission(Permission.WRITE_EXTRACTION)
require_admin_api_keys = require_permission(Permission.ADMIN_API_KEYS)
require_admin_users = require_permission(Permission.ADMIN_USERS)
require_admin_tenants = require_permission(Permission.ADMIN_TENANTS)

# Merged from root shared/identity/dependencies.py
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
        context: RequestContext = Depends(get_current_context),
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
            
            # Task 2: Initialize privileged session tracking
            if context.privileged_session_start is None:
                context.privileged_session_start = time.time()
            
            # Log the privileged access attempt
            logger.warning(
                "Privileged access by super_admin: user=%s tenant=%s reason=%s endpoint=%s",
                context.user_id,
                context.tenant_id,
                reason,
                request.url.path,
            )
            
            # Task 2: Emit CROSS_TENANT_ACCESS audit event
            try:
                session_duration = int(time.time() - context.privileged_session_start) if context.privileged_session_start else 0
                
                audit_details = PrivilegedAccessDetails(
                    accessed_tenant_ids=list(context.accessed_tenant_ids),
                    resource_types=["cross_tenant_query"],  # Will be updated by actual queries
                    session_duration_seconds=session_duration,
                    reason=reason,
                    approval_ticket=request.headers.get("X-Approval-Ticket"),
                    query_count=len(context.accessed_tenant_ids),
                )
                
                await emit_audit_event(
                    action=AuditAction.CROSS_TENANT_ACCESS,
                    outcome=AuditOutcome.SUCCESS,
                    actor_id=context.user_id,
                    actor_type="super_admin",
                    tenant_id=context.tenant_id,
                    resource_type="privileged_session",
                    resource_id=str(request.url.path),
                    request_id=context.request_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("User-Agent"),
                    details=audit_details.model_dump(),
                )
            except Exception as e:
                logger.error(f"Failed to emit privileged access audit event: {e}")
                # Don't block the request if audit fails, but log it

        return context

    return _check_privileged

def validate_jwt_config() -> None:
    """Validate JWT configuration for production safety.
    
    Raises:
        ValueError: If JWT is misconfigured in production
    """
    environment = os.getenv("ENVIRONMENT", "").lower()
    jwt_secret = os.getenv("JWT_SECRET", "")
    jwt_issuer = os.getenv("JWT_ISSUER", "")
    jwt_audience = os.getenv("JWT_AUDIENCE", "")
    
    if environment == "production":
        if not jwt_secret:
            raise ValueError(
                "JWT_SECRET is required in production. "
                "Tokens cannot be verified without a secret."
            )
        
        if len(jwt_secret) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters in production. "
                "Weak secrets are vulnerable to brute force attacks."
            )
        
        if not jwt_issuer:
            raise ValueError(
                "JWT_ISSUER is required in production. "
                "Missing issuer allows tokens from any source to be accepted."
            )
        
        if not jwt_audience:
            raise ValueError(
                "JWT_AUDIENCE is required in production. "
                "Missing audience allows tokens intended for other services."
            )
