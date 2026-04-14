"""Database engine and session management.

P0-08: Supports PostgreSQL Row-Level Security via SET LOCAL app.tenant_id
SECURITY: Fail-safe tenant isolation - tenant context is mandatory
"""

from collections.abc import Generator
from contextlib import contextmanager
from uuid import UUID

from fastapi import Header, HTTPException, status
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

# Create engine
engine = create_engine(
    settings.database_url, pool_size=5, max_overflow=10, pool_pre_ping=True, echo=settings.debug
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TenantContextError(Exception):
    """Raised when tenant context is missing or invalid in fail-safe mode."""
    pass


# SECURITY: Fail-safe mode - require explicit tenant context
# Set to False only for admin/system operations with proper role validation
FAIL_SAFE_MODE = True


def validate_tenant_id(tenant_id: UUID | str | None) -> str:
    """Validate tenant_id format and return normalized string.
    
    SECURITY: Strict validation to prevent tenant confusion attacks.
    
    Args:
        tenant_id: Tenant identifier to validate
        
    Returns:
        Normalized tenant ID string
        
    Raises:
        TenantContextError: If tenant_id is invalid or missing in fail-safe mode
    """
    if tenant_id is None:
        if FAIL_SAFE_MODE:
            raise TenantContextError(
                "Tenant context is mandatory in fail-safe mode. "
                "Use explicit admin role context for system operations."
            )
        return ""
    
    # Convert to string and normalize
    normalized = str(tenant_id).strip()
    
    # Fail-safe: empty tenant_id is not allowed
    if not normalized:
        raise TenantContextError(
            "Empty tenant_id is not allowed. Provide a valid tenant context."
        )
    
    # Validate UUID format for strict tenant isolation
    if normalized.lower() not in ('system', 'admin', 'internal'):
        try:
            UUID(normalized)
        except ValueError:
            raise TenantContextError(
                f"Invalid tenant_id format: {normalized}. Expected UUID."
            )
    
    return normalized


def set_tenant_context(session: Session, tenant_id: UUID | str | None) -> None:
    """P0-08: Set PostgreSQL app.tenant_id for RLS policies.
    
    SECURITY: Fail-safe semantics - tenant context is mandatory unless
    explicitly using admin bypass with proper role authentication.

    Executes SET LOCAL app.tenant_id = '...' which applies for the
    duration of the current transaction. RLS policies in PostgreSQL
    can reference current_setting('app.tenant_id') to filter rows.

    Args:
        session: SQLAlchemy session
        tenant_id: Tenant UUID or string identifier (whitespace is stripped)
        
    Raises:
        TenantContextError: If tenant_id is missing/invalid in fail-safe mode
    """
    # SECURITY: Validate tenant context with fail-safe semantics
    normalized_id = validate_tenant_id(tenant_id)
    
    # Set tenant context for RLS policies
    # Empty string only allowed for admin roles (enforced by RLS policy TO clause)
    session.execute(
        text("SET LOCAL app.tenant_id = :tenant_id"),
        {"tenant_id": normalized_id}
    )


@contextmanager
def get_db_session(
    tenant_id: UUID | str | None = None,
    *,
    require_tenant: bool = True
) -> Generator[Session, None, None]:
    """Get a database session as a context manager.

    SECURITY: Fail-safe by default - tenant context is mandatory.

    Args:
        tenant_id: Tenant ID to set for RLS context (P0-08)
        require_tenant: If True (default), enforce mandatory tenant context.
                       Set to False only for admin/system operations with
                       proper role authentication.
    
    Raises:
        TenantContextError: If tenant_id is missing/invalid and require_tenant=True
    """
    # SECURITY: Enforce mandatory tenant context by default
    if require_tenant and tenant_id is None:
        raise TenantContextError(
            "Database session requires explicit tenant context. "
            "Pass tenant_id or use require_tenant=False for admin operations."
        )
    
    session = SessionLocal()
    try:
        # P0-08: Set tenant context for RLS (fail-safe validation)
        set_tenant_context(session, tenant_id)
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions (without RLS).
    
    SECURITY: Deprecated - use get_db_with_tenant for production code.
    This bypasses tenant isolation and should only be used for:
    - Health checks
    - Admin operations with proper role authentication
    """
    with get_db_session(require_tenant=False) as session:
        yield session


def get_db_with_tenant(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID", description="Tenant UUID for RLS isolation")
) -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session with RLS tenant context.
    
    SECURITY: Mandatory tenant context - X-Tenant-ID header is required.
    Fail-safe: Rejects requests without explicit tenant identification.

    Automatically extracts X-Tenant-ID header and sets PostgreSQL app.tenant_id
    for Row-Level Security policies.

    Usage::

        @router.get("/jobs/{id}")
        async def get_job(id: UUID, db: Session = Depends(get_db_with_tenant)):
            ...
    
    Raises:
        HTTPException: 400 if X-Tenant-ID header is missing or invalid
    """
    # SECURITY: Fail-fast on missing tenant header
    if not x_tenant_id or not x_tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required for tenant isolation",
        )
    
    try:
        # Validate UUID format for strict tenant isolation
        UUID(x_tenant_id.strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID must be a valid UUID",
        )
    
    with get_db_session(tenant_id=x_tenant_id, require_tenant=True) as session:
        yield session


def get_db_with_tenant_from_context(
    tenant_id: UUID | str | None = None
) -> Generator[Session, None, None]:
    """
    Context manager for database sessions with RLS tenant context.
    For use outside FastAPI request lifecycle (e.g., background tasks).

    Usage::

        with get_db_with_tenant_from_context(tenant_id=tenant_uuid) as db:
            ...
    """
    with get_db_session(tenant_id=tenant_id) as session:
        yield session
