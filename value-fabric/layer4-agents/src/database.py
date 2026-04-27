"""
Async SQLAlchemy engine and session management for Layer 4.

Extends the checkpoint database configuration to support operational data storage
for accounts, CRM sync metadata, and workflow state.

P0-08: Supports PostgreSQL Row-Level Security via SET LOCAL app.tenant_id
SECURITY: Fail-safe tenant isolation - tenant context is mandatory
"""

from __future__ import annotations

import logging
import os
import warnings
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

# Task 4.1: Default isolation tier constant
DEFAULT_ISOLATION_TIER = "shared"

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# P1: Module-level logger for audit emission errors
logger = logging.getLogger(__name__)

# Task 1.6: Tenant context validation metrics
_tenant_validation_metrics = {
    "validations_total": 0,
    "validation_failures": 0,
    "uuid_format_errors": 0,
    "missing_context_errors": 0,
    "empty_tenant_errors": 0,
}


def get_tenant_validation_metrics() -> dict[str, int]:
    """Get tenant validation metrics for monitoring.
    
    Returns:
        Dictionary of validation metric counters
    """
    return _tenant_validation_metrics.copy()


def reset_tenant_validation_metrics() -> None:
    """Reset tenant validation metrics. Used for testing."""
    _tenant_validation_metrics.update({
        "validations_total": 0,
        "validation_failures": 0,
        "uuid_format_errors": 0,
        "missing_context_errors": 0,
        "empty_tenant_errors": 0,
    })


try:
    from shared.identity.context import RequestContext
    from shared.identity.dependencies import get_request_context
    SHARED_IDENTITY_AVAILABLE = True
except ImportError:
    SHARED_IDENTITY_AVAILABLE = False
    RequestContext = None  # type: ignore
    get_request_context = None  # type: ignore

# Task 3.1: Tenant resolution audit logging
try:
    from shared.audit import emit_audit_event, AuditAction, AuditOutcome, TenantContextSetDetails
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False
    emit_audit_event = None  # type: ignore
    AuditAction = None  # type: ignore
    AuditOutcome = None  # type: ignore
    TenantContextSetDetails = None  # type: ignore


async def _emit_tenant_context_set_audit(
    context: "RequestContext",
    tenant_id: str | None,
    *,
    is_bypass: bool = False,
    bypass_reason: str | None = None,
) -> None:
    """P1: Helper to emit TENANT_CONTEXT_SET audit event.

    Centralizes the audit emission logic to avoid duplication between
    get_db_from_context and get_db_with_optional_tenant.
    """
    if not AUDIT_AVAILABLE:
        return

    try:
        details = TenantContextSetDetails(
            tenant_id=tenant_id,
            isolation_tier=context.isolation_tier,
            bypass=is_bypass,
            bypass_reason=bypass_reason,
            context_source="request_context",
        )
        await emit_audit_event(
            action=AuditAction.TENANT_CONTEXT_SET,
            outcome=AuditOutcome.SUCCESS,
            resource_type="database_session",
            resource_id=tenant_id,
            actor_id=context.user_id or context.api_key_id or context.service_account_id,
            tenant_id=context.tenant_id,
            request_id=context.request_id,
            details=details.model_dump(exclude_none=True),
        )
    except Exception as e:
        # P0: Log debug only - don't fail the request
        logger.debug("Tenant context audit emission failed (non-critical): %s", e)


# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared declarative base for all Layer 4 models."""

    pass


# ---------------------------------------------------------------------------
# Engine — created once at import time, reused across requests
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    """Get database URL from environment.

    Falls back to checkpoint database URL for compatibility,
    but allows separate configuration for operational data.
    """
    return os.getenv(
        "LAYER4_DATABASE_URL",
        os.getenv(
            "CHECKPOINT_DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@postgres:5432/layer4_agents",
        ),
    )


def get_engine() -> AsyncEngine:
    """Return (or lazily create) the shared async engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_database_url(),
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False,
            future=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return (or lazily create) the shared session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _session_factory


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


class TenantContextError(Exception):
    """Raised when tenant context is missing or invalid in fail-safe mode."""
    pass


# SECURITY: Fail-safe mode - require explicit tenant context
# Set to False only for admin/system operations with proper role validation
FAIL_SAFE_MODE = True

# Reserved tenant keywords for system/admin operations
RESERVED_TENANT_KEYWORDS = frozenset({'system', 'admin', 'internal'})


def validate_tenant_id(tenant_id: UUID | str | None) -> str:
    """Validate tenant_id format and return normalized string.
    
    SECURITY: Strict validation to prevent tenant confusion attacks.
    Tracks metrics for validation monitoring.
    
    Args:
        tenant_id: Tenant identifier to validate (UUID object, UUID string, or None)
        
    Returns:
        Normalized tenant ID string (lowercase UUID format or reserved keyword)
        
    Raises:
        TenantContextError: If tenant_id is invalid or missing in fail-safe mode
    
    Examples:
        >>> validate_tenant_id(UUID('550e8400-e29b-41d4-a716-446655440000'))
        '550e8400-e29b-41d4-a716-446655440000'
        >>> validate_tenant_id('system')
        'system'
    """
    _tenant_validation_metrics["validations_total"] += 1
    
    if tenant_id is None:
        _tenant_validation_metrics["missing_context_errors"] += 1
        _tenant_validation_metrics["validation_failures"] += 1
        if FAIL_SAFE_MODE:
            raise TenantContextError(
                "Tenant context is mandatory. Ensure request includes valid tenant_id "
                "in JWT token or X-Tenant-ID header. For admin operations, use "
                "get_db_with_optional_tenant() with require_super_admin() dependency."
            )
        return ""
    
    # Convert to string and normalize
    normalized = str(tenant_id).strip()
    
    # Fail-safe: empty tenant_id is not allowed
    if not normalized:
        _tenant_validation_metrics["empty_tenant_errors"] += 1
        _tenant_validation_metrics["validation_failures"] += 1
        raise TenantContextError(
            "Empty tenant_id is not allowed. Provide a valid tenant context."
        )
    
    # Validate UUID format for strict tenant isolation
    if normalized.lower() not in RESERVED_TENANT_KEYWORDS:
        try:
            UUID(normalized)
        except ValueError:
            _tenant_validation_metrics["uuid_format_errors"] += 1
            _tenant_validation_metrics["validation_failures"] += 1
            raise TenantContextError(
                f"Invalid tenant_id format: '{normalized}'. Expected valid UUID or "
                f"reserved keyword ({', '.join(sorted(RESERVED_TENANT_KEYWORDS))})."
            )
    
    return normalized


async def set_tenant_context(session: AsyncSession, tenant_id: UUID | str | None) -> None:
    """P0-08: Set PostgreSQL app.tenant_id for RLS policies.
    
    SECURITY: Fail-safe semantics - tenant context is mandatory unless
    explicitly using admin bypass with proper role authentication.

    Executes SET LOCAL app.tenant_id = '...' which applies for the
    duration of the current transaction. RLS policies in PostgreSQL
    can reference current_setting('app.tenant_id') to filter rows.

    Args:
        session: SQLAlchemy async session
        tenant_id: Tenant UUID or string identifier (whitespace is stripped)
        
    Raises:
        TenantContextError: If tenant_id is missing/invalid in fail-safe mode
    """
    # SECURITY: Validate tenant context with fail-safe semantics
    normalized_id = validate_tenant_id(tenant_id)
    
    # Set tenant context for RLS policies
    # Empty string only allowed for admin roles (enforced by RLS policy TO clause)
    await session.execute(
        text("SET LOCAL app.tenant_id = :tenant_id"),
        {"tenant_id": normalized_id}
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions (without RLS).

    DEPRECATED: Use get_db_from_context() for all new endpoints.
    This function is kept only for health checks and will be removed.

    SECURITY: Use only for health checks or admin operations with proper
    role authentication. All production endpoints should use get_db_from_context.
    """
    warnings.warn(
        "get_db() is deprecated. Use get_db_from_context() for proper tenant isolation.",
        DeprecationWarning,
        stacklevel=2,
    )
    # SECURITY: Bypass tenant validation for health checks (admin role required in DB)
    factory = get_session_factory()
    async with factory() as session:
        # Clear tenant context - RLS bypass only works for admin/system roles
        await session.execute(text("SET LOCAL app.tenant_id = ''"))
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_with_tenant(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID", description="Tenant UUID for RLS isolation")
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session with RLS tenant context.

    DEPRECATED: Use get_db_from_context() which extracts tenant from RequestContext
    set by GovernanceMiddleware. This direct header parsing is error-prone.

    SECURITY: Mandatory tenant context - X-Tenant-ID header is required.
    Fail-safe: Rejects requests without explicit tenant identification.

    Automatically extracts X-Tenant-ID header and sets PostgreSQL app.tenant_id
    for Row-Level Security policies.

    Usage::

        @router.get("/accounts/{id}")
        async def get_account(id: UUID, db: AsyncSession = Depends(get_db_with_tenant)):
            ...

    Raises:
        HTTPException: 400 if X-Tenant-ID header is missing or invalid
    """
    warnings.warn(
        "get_db_with_tenant() is deprecated. Use get_db_from_context() for proper tenant context propagation.",
        DeprecationWarning,
        stacklevel=2,
    )
    try:
        # SECURITY: Fail-safe validation via validate_tenant_id
        # This checks for empty values and validates UUID format
        validate_tenant_id(x_tenant_id)
    except TenantContextError as e:
        # Convert TenantContextError to HTTP 400 for FastAPI
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    
    factory = get_session_factory()
    async with factory() as session:
        # P0-08: Set tenant context for RLS (already validated above)
        await session.execute(
            text("SET LOCAL app.tenant_id = :tenant_id"),
            {"tenant_id": x_tenant_id}
        )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_from_context(
    context: "RequestContext" = Depends(get_request_context),  # type: ignore
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields DB session with tenant context from RequestContext (Task 1.2).

    This is the recommended dependency for new endpoints. It extracts tenant_id
    from the RequestContext (set by GovernanceMiddleware) rather than directly
    from headers, ensuring consistent tenant resolution.

    Usage::

        @router.get("/items")
        async def list_items(
            db: AsyncSession = Depends(get_db_from_context),
            context: RequestContext = Depends(get_request_context)
        ):
            ...

    Raises:
        HTTPException: 400 if tenant context is missing in RequestContext
    """
    if not SHARED_IDENTITY_AVAILABLE:
        raise RuntimeError("shared.identity package required for get_db_from_context")

    if not context or not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required. Ensure request has passed through GovernanceMiddleware.",
        )

    # SECURITY: Fail-safe validation via validate_tenant_id
    try:
        tenant_id = validate_tenant_id(context.tenant_id)
    except TenantContextError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    factory = get_session_factory()
    async with factory() as session:
        # P0-08: Set tenant context for RLS with isolation tier awareness
        # Currently only 'shared' tier is supported (RLS-based)
        if context.isolation_tier == "shared":
            await session.execute(
                text("SET LOCAL app.tenant_id = :tenant_id"),
                {"tenant_id": tenant_id}
            )
        else:
            # Future: handle 'schema' and 'database' tiers
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Isolation tier '{context.isolation_tier}' not yet implemented",
            )

        # Task 3.1: Emit tenant context set audit event
        await _emit_tenant_context_set_audit(context, str(tenant_id), is_bypass=False)

        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_with_optional_tenant(
    context: "RequestContext" = Depends(get_request_context),  # type: ignore
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for DB sessions with optional tenant context (Task 1.3).

    DEPRECATED: Use get_db_from_context() combined with require_super_admin() for
    admin operations. This separate function creates inconsistency in tenant handling.

    This is for super-admin operations that may cross tenant boundaries.
    For regular endpoints, use get_db_from_context() which enforces tenant context.

    Security: Must be combined with require_privileged_access() or require_super_admin()
    dependencies to ensure only authorized users can bypass tenant isolation.

    Usage::

        @router.get("/admin/all-tenants")
        async def get_all_tenants(
            db: AsyncSession = Depends(get_db_with_optional_tenant),
            context: RequestContext = Depends(require_privileged_access()),
        ):
            ...

    Raises:
        HTTPException: 400 if non-super-admin tries to use without tenant context
    """
    warnings.warn(
        "get_db_with_optional_tenant() is deprecated. Use get_db_from_context() for consistency.",
        DeprecationWarning,
        stacklevel=2,
    )
    if not SHARED_IDENTITY_AVAILABLE:
        raise RuntimeError("shared.identity package required for get_db_with_optional_tenant")

    factory = get_session_factory()
    async with factory() as session:
        # Super admins can bypass tenant context (empty tenant_id for RLS)
        is_bypass = False
        bypass_reason = None
        effective_tenant_id = None

        if context.is_super_admin():
            await session.execute(text("SET LOCAL app.tenant_id = ''"))
            is_bypass = True
            bypass_reason = "super_admin_bypass"
            effective_tenant_id = ""
        elif context.tenant_id:
            # Regular users must have tenant context
            try:
                effective_tenant_id = validate_tenant_id(context.tenant_id)
            except TenantContextError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                ) from e
            await session.execute(
                text("SET LOCAL app.tenant_id = :tenant_id"),
                {"tenant_id": effective_tenant_id}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context required. Use get_db_from_context for endpoints requiring tenant isolation.",
            )

        # Task 3.1: Emit tenant context set audit event (with bypass flag for super-admin)
        await _emit_tenant_context_set_audit(
            context,
            effective_tenant_id if effective_tenant_id else None,
            is_bypass=is_bypass,
            bypass_reason=bypass_reason,
        )

        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Tier-aware database session factory (Task 4.1)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def get_tiered_db_session(
    tenant_id: UUID | str,
    isolation_tier: str = DEFAULT_ISOLATION_TIER,
    *,
    request_context: "RequestContext" | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session with appropriate isolation based on tenant tier.

    DEPRECATED: Use get_db_from_context() which handles tier awareness internally.
    This separate factory is redundant and creates confusion about which to use.

    This factory routes to the correct session implementation based on
    the tenant's isolation tier:
    - "shared": Uses RLS with SET LOCAL app.tenant_id
    - "schema": Reserved for future implementation (dedicated schema)
    - "database": Reserved for future implementation (dedicated database)

    Args:
        tenant_id: The tenant UUID
        isolation_tier: One of "shared", "schema", "database"
        request_context: Optional RequestContext for audit logging

    Raises:
        HTTPException: 501 if unimplemented tier requested
        TenantContextError: If tenant_id is invalid
    """
    warnings.warn(
        "get_tiered_db_session() is deprecated. Use get_db_from_context() for consistency.",
        DeprecationWarning,
        stacklevel=2,
    )
    # Validate tenant ID
    validated_id = validate_tenant_id(tenant_id)

    # Route to appropriate session implementation
    if isolation_tier == "shared":
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(
                text("SET LOCAL app.tenant_id = :tenant_id"),
                {"tenant_id": validated_id}
            )

            # Emit audit event if context provided
            if request_context and AUDIT_AVAILABLE:
                await _emit_tenant_context_set_audit(
                    request_context,
                    validated_id,
                    is_bypass=False,
                    bypass_reason=None,
                )

            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    elif isolation_tier == "schema":
        # Future: Implement schema-per-tenant routing
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Schema-per-tenant isolation tier not yet implemented",
        )

    elif isolation_tier == "database":
        # Future: Implement database-per-tenant routing
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Database-per-tenant isolation tier not yet implemented",
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown isolation tier: {isolation_tier}",
        )


# ---------------------------------------------------------------------------
# Context manager for non-FastAPI usage (services, background tasks)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def db_session(
    tenant_id: UUID | str | None = None,
    *,
    require_tenant: bool = True
) -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for use outside of FastAPI request lifecycle.

    DEPRECATED: Use get_db_from_context() with FastAPI's Depends() for all
    endpoint handlers. For background tasks, inject RequestContext explicitly.

    SECURITY: Fail-safe by default - tenant context is mandatory.

    Args:
        tenant_id: Tenant ID to set for RLS context (P0-08)
        require_tenant: If True (default), enforce mandatory tenant context.
                       Set to False only for admin/system operations with
                       proper role authentication.

    Raises:
        TenantContextError: If tenant_id is missing/invalid and require_tenant=True
    """
    warnings.warn(
        "db_session() is deprecated. Use get_db_from_context() for consistency.",
        DeprecationWarning,
        stacklevel=2,
    )
    # SECURITY: Enforce mandatory tenant context by default
    if require_tenant:
        # This will raise TenantContextError in fail-safe mode if tenant_id is invalid
        tenant_id = validate_tenant_id(tenant_id)
    elif tenant_id is not None:
        # Validate even when require_tenant=False, if a tenant_id was provided
        tenant_id = validate_tenant_id(tenant_id)
    # If require_tenant=False and tenant_id is None, we skip validation (admin bypass)
    
    factory = get_session_factory()
    async with factory() as session:
        # P0-08: Set tenant context for RLS
        # Empty string for admin bypass, validated tenant_id otherwise
        normalized = str(tenant_id) if tenant_id is not None else ""
        await session.execute(
            text("SET LOCAL app.tenant_id = :tenant_id"),
            {"tenant_id": normalized}
        )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Lifecycle helpers (called from FastAPI lifespan)
# ---------------------------------------------------------------------------


async def init_db() -> None:
    """Create all tables if they do not exist (dev/test convenience)."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose the engine connection pool on shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
