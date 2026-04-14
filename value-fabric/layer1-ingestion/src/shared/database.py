"""Database engine and session management.

P0-08: Supports PostgreSQL Row-Level Security via SET LOCAL app.tenant_id
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Optional
from uuid import UUID

from fastapi import Header
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

# Create engine
engine = create_engine(
    settings.database_url, pool_size=5, max_overflow=10, pool_pre_ping=True, echo=settings.debug
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def set_tenant_context(session: Session, tenant_id: Optional[UUID | str]) -> None:
    """P0-08: Set PostgreSQL app.tenant_id for RLS policies.

    Executes SET LOCAL app.tenant_id = '...' which applies for the
    duration of the current transaction. RLS policies in PostgreSQL
    can reference current_setting('app.tenant_id') to filter rows.

    Args:
        session: SQLAlchemy session
        tenant_id: Tenant UUID or string identifier
    """
    if tenant_id:
        # Use SET LOCAL - only affects current transaction
        session.execute(
            text("SET LOCAL app.tenant_id = :tenant_id"),
            {"tenant_id": str(tenant_id)}
        )
    else:
        # Clear tenant context for system-level operations
        session.execute(text("SET LOCAL app.tenant_id = ''"))


@contextmanager
def get_db_session(tenant_id: Optional[UUID | str] = None) -> Generator[Session, None, None]:
    """Get a database session as a context manager.

    Args:
        tenant_id: Optional tenant ID to set for RLS context (P0-08)
    """
    session = SessionLocal()
    try:
        # P0-08: Set tenant context for RLS if provided
        if tenant_id:
            set_tenant_context(session, tenant_id)
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions (without RLS)."""
    with get_db_session() as session:
        yield session


def get_db_with_tenant(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session with RLS tenant context.

    Automatically extracts X-Tenant-ID header and sets PostgreSQL app.tenant_id
    for Row-Level Security policies.

    Usage::

        @router.get("/jobs/{id}")
        async def get_job(id: UUID, db: Session = Depends(get_db_with_tenant)):
            ...
    """
    with get_db_session(tenant_id=x_tenant_id) as session:
        yield session
