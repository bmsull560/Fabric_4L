"""Neo4j-aware tenant dependencies for Layer 3 Knowledge Graph (Sprint 5).

This module provides FastAPI dependencies that extract tenant context from
RequestContext and apply Neo4j-specific tenant enforcement through composite
constraints (id, tenant_id) and query scoping.
"""

from __future__ import annotations

import logging
import inspect
import re
from typing import TYPE_CHECKING, Any

from fastapi import Depends, HTTPException, Request, status

if TYPE_CHECKING:
    from value_fabric.shared.identity.context import RequestContext

from .dependencies import get_neo4j_driver
from value_fabric.shared.identity.protocols import ProviderUnavailableError, RequestContextProvider

try:
    from value_fabric.shared.identity.isolation import (
        DEFAULT_TENANT_LABEL_POLICY,
        QueryScope,
        ScopedQuery,
    )
    TENANT_ISOLATION_AVAILABLE = True
except ImportError:
    DEFAULT_TENANT_LABEL_POLICY = None  # type: ignore[assignment]
    QueryScope = None  # type: ignore[assignment]
    ScopedQuery = None  # type: ignore[assignment]
    TENANT_ISOLATION_AVAILABLE = False

logger = logging.getLogger(__name__)

_LABEL_PATTERN = re.compile(
    r"\b(?:MATCH|OPTIONAL\s+MATCH|MERGE|CREATE)\s*\([^)]*:\s*([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE | re.DOTALL,
)


def _tenant_labels_in_query(query: str) -> set[str]:
    if DEFAULT_TENANT_LABEL_POLICY is None:
        return set()
    return {
        label
        for label in _LABEL_PATTERN.findall(query)
        if DEFAULT_TENANT_LABEL_POLICY.is_tenant_owned(label)
    }


def _query_has_tenant_predicate(query: str) -> bool:
    return any(marker in query for marker in (".tenant_id", ".tenantId", "$tenant_id", "$_tenant_id", "$tenantId"))


try:
    from value_fabric.shared.identity.context import RequestContext
    from value_fabric.shared.identity.dependencies import get_current_context
    SHARED_IDENTITY_AVAILABLE = True
except ImportError:
    SHARED_IDENTITY_AVAILABLE = False
    RequestContext = None  # type: ignore[assignment]
    get_current_context = None


try:
    from value_fabric.shared.audit import AuditAction, AuditOutcome, emit_audit_event
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False
    emit_audit_event = None
    AuditAction = None
    AuditOutcome = None

_context_provider: RequestContextProvider | None = get_current_context


def _require_context_provider() -> RequestContextProvider:
    if _context_provider is None:
        raise ProviderUnavailableError(
            provider="value_fabric.shared.identity.dependencies.get_current_context",
            code="IDENTITY_PROVIDER_UNAVAILABLE",
            detail="shared.identity is required for tenant-aware Neo4j dependencies.",
        )
    return _context_provider


class Neo4jTenantSession:
    """Wrapper for Neo4j session with tenant context enforcement.

    This class wraps a Neo4j async session and provides methods that
    automatically include tenant_id in queries for RLS-like enforcement.

    Example:
        async with get_neo4j_with_tenant(request) as neo4j:
            result = await neo4j.run(
                "MATCH (n {id: $id, tenant_id: $tenant_id}) RETURN n",
                id=entity_id
            )
    """

    def __init__(self, session, tenant_id: str | None, is_bypass: bool = False):
        self._session = session
        self._tenant_id = tenant_id
        self._is_bypass = is_bypass

    @property
    def tenant_id(self) -> str | None:
        return self._tenant_id

    @property
    def is_bypass(self) -> bool:
        return self._is_bypass

    async def run(self, query: Any, parameters: dict | None = None, **kwparameters) -> Any:
        """Run Neo4j Cypher through the strict tenant-aware boundary.

        Tenant-facing code should pass a ``ScopedQuery`` created by
        ``TenantScopedCypher``. Backward-compatible raw Cypher remains allowed
        only when tenant-owned labels include explicit tenant predicates and a
        tenant context is present. This is a fail-closed guardrail rather than a
        text-rewriting mechanism.
        """
        params = dict(parameters or {})
        params.update(kwparameters)

        if TENANT_ISOLATION_AVAILABLE and isinstance(query, ScopedQuery):
            if query.scope == QueryScope.TENANT:
                scoped_tenant = query.tenant_id or self._tenant_id
                if not scoped_tenant or self._is_bypass:
                    raise ValueError("Tenant-scoped Cypher requires a non-bypass tenant context")
                params = {**query.params, **params}
                params.setdefault("tenant_id", scoped_tenant)
                params.setdefault("_tenant_id", scoped_tenant)
            elif not self._is_bypass and query.scope != QueryScope.HEALTH:
                logger.info(
                    "Executing reviewed %s scoped Neo4j operation %s",
                    query.scope,
                    query.operation,
                )
                params = {**query.params, **params}
            else:
                params = {**query.params, **params}
            return await self._session.run(query.cypher, params)

        query_text = str(query)
        labels = _tenant_labels_in_query(query_text)
        if labels and not self._is_bypass:
            if not self._tenant_id:
                raise ValueError(f"Tenant context is required for tenant-owned labels: {sorted(labels)}")
            if not _query_has_tenant_predicate(query_text):
                raise ValueError(
                    "Raw Cypher touching tenant-owned labels must include explicit tenant predicates"
                )
            params.setdefault("tenant_id", self._tenant_id)
            params.setdefault("_tenant_id", self._tenant_id)
        elif self._tenant_id and not self._is_bypass:
            params.setdefault("tenant_id", self._tenant_id)
            params.setdefault("_tenant_id", self._tenant_id)

        return await self._session.run(query_text, params)

    def _create_tenant_tx(self, tx) -> Any:
        """Create a tenant-aware transaction wrapper.
        
        Extracted to avoid duplication between read_transaction and write_transaction.
        """
        class TenantTx:
            def __init__(self, inner_tx, tenant_id: str | None):
                self._tx = inner_tx
                self._tenant_id = tenant_id

            async def run(self, query, parameters=None, **kwargs):
                params = dict(parameters or {})
                params.update(kwargs)
                if TENANT_ISOLATION_AVAILABLE and isinstance(query, ScopedQuery):
                    if query.scope == QueryScope.TENANT:
                        scoped_tenant = query.tenant_id or self._tenant_id
                        if not scoped_tenant:
                            raise ValueError("Tenant-scoped Cypher requires tenant context")
                        params = {**query.params, **params}
                        params.setdefault("tenant_id", scoped_tenant)
                        params.setdefault("_tenant_id", scoped_tenant)
                    else:
                        params = {**query.params, **params}
                    return await self._tx.run(query.cypher, params)

                query_text = str(query)
                labels = _tenant_labels_in_query(query_text)
                if labels:
                    if not self._tenant_id:
                        raise ValueError(f"Tenant context is required for tenant-owned labels: {sorted(labels)}")
                    if not _query_has_tenant_predicate(query_text):
                        raise ValueError(
                            "Raw Cypher touching tenant-owned labels must include explicit tenant predicates"
                        )
                if self._tenant_id:
                    params.setdefault("tenant_id", self._tenant_id)
                    params.setdefault("_tenant_id", self._tenant_id)
                return await self._tx.run(query_text, params)

        return TenantTx(tx, self._tenant_id)

    async def read_transaction(self, callback) -> Any:
        """Execute a read transaction with tenant context."""
        async def wrapped_callback(tx):
            tenant_tx = self._create_tenant_tx(tx)
            return await callback(tenant_tx)

        return await self._session.read_transaction(wrapped_callback)

    async def write_transaction(self, callback) -> Any:
        """Execute a write transaction with tenant context."""
        async def wrapped_callback(tx):
            tenant_tx = self._create_tenant_tx(tx)
            return await callback(tenant_tx)

        return await self._session.write_transaction(wrapped_callback)

    async def close(self):
        """Close the underlying session."""
        await self._session.close()

    async def __aenter__(self):
        return self

    async def execute_query(self, query: Any, parameters: dict | None = None, **kwparameters) -> list[dict]:
        """Execute a Cypher query and return records as a list of dicts.

        This mirrors the driver-level ``execute_query`` API but scopes
        parameters through the tenant session wrapper.
        """
        params = parameters or {}
        params.update(kwparameters)
        result = await self.run(query, params)
        records = []
        async for record in result:
            records.append(record.data())
        return records

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def create_neo4j_tenant_session(tenant_id: str | None) -> Neo4jTenantSession:
    """Create a Neo4jTenantSession from an explicit tenant_id string.

    For route modules that extract tenant_id through their own auth
    mechanisms (API keys, custom JWT) rather than GovernanceMiddleware.

    Usage::

        tenant_id = getattr(api_key, "tenant_id", None)
        async with await create_neo4j_tenant_session(tenant_id) as neo4j:
            result = await neo4j.run(
                "MATCH (n {id: $id, tenant_id: $tenant_id}) RETURN n",
                id=entity_id,
            )

    Note:
        The caller is responsible for closing the session. Use ``async with``
        or call ``await neo4j.close()`` explicitly.
    """
    if not tenant_id:
        raise ValueError("tenant_id is required for tenant-scoped sessions")
    from ..db.driver import get_driver

    driver = await get_driver()
    session = driver.session()
    return Neo4jTenantSession(session=session, tenant_id=tenant_id, is_bypass=False)


async def get_neo4j_with_tenant(
    request: Request,
    context: RequestContext | None = Depends(_require_context_provider()),
) -> Neo4jTenantSession:
    """FastAPI dependency for Neo4j session with tenant context (Sprint 5).

    SECURITY: Extracts tenant_id from RequestContext (set by GovernanceMiddleware).
    Creates a Neo4jTenantSession that automatically scopes queries to the tenant.

    Usage::

        @router.get("/entity/{entity_id}")
        async def get_entity(
            entity_id: str,
            neo4j: Neo4jTenantSession = Depends(get_neo4j_with_tenant),
        ):
            result = await neo4j.run(
                "MATCH (n {id: $id, tenant_id: $tenant_id}) RETURN n",
                id=entity_id,
            )

    Raises:
        HTTPException: 400 if tenant context is missing
        HTTPException: 503 if Neo4j is unavailable
    """
    if not SHARED_IDENTITY_AVAILABLE:
        _require_context_provider()

    if not context or not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required. Ensure request passed through GovernanceMiddleware.",
        )

    session = None
    try:
        driver = get_neo4j_driver()
        session = driver.session()
    except Exception as e:
        logger.error("Failed to create Neo4j session: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j service unavailable. Please try again later.",
        ) from e

    try:
        # Emit audit event for tenant context access
        if AUDIT_AVAILABLE and emit_audit_event:
            try:
                await emit_audit_event(
                    action=AuditAction.TENANT_CONTEXT_SET,
                    outcome=AuditOutcome.SUCCESS,
                    resource_type="neo4j_session",
                    resource_id=str(context.tenant_id),
                    actor_id=context.user_id or context.api_key_id or context.service_account_id,
                    tenant_id=context.tenant_id,
                    request_id=context.request_id,
                    details={
                        "isolation_tier": context.isolation_tier,
                        "auth_source": context.auth_source,
                    },
                )
            except Exception as e:
                logger.debug("Audit emission failed (non-critical): %s", e)

        return Neo4jTenantSession(
            session=session,
            tenant_id=str(context.tenant_id),
            is_bypass=False,
        )
    except Exception:
        # Ensure session is closed if audit event or other initialization fails
        if session is not None:
            try:
                await session.close()
            except Exception as close_error:
                logger.warning("Failed to close Neo4j session after error: %s", close_error)
        raise


async def get_neo4j_with_optional_tenant(
    request: Request,
    context: RequestContext | None = Depends(_require_context_provider()),
) -> Neo4jTenantSession:
    """Neo4j session with optional tenant for super-admin operations (Sprint 5).

    SECURITY: Must be combined with privileged access checks.
    Super-admins can bypass tenant scoping for cross-tenant graph operations.

    Usage::

        @router.get("/admin/graph-stats")
        async def get_graph_stats(
            neo4j: Neo4jTenantSession = Depends(get_neo4j_with_optional_tenant),
        ):
            # Super-admin sees all tenants
            result = await neo4j.run("MATCH (n) RETURN count(n)")

    Raises:
        HTTPException: 400 if non-super-admin without tenant context
        HTTPException: 503 if Neo4j is unavailable
    """
    if not SHARED_IDENTITY_AVAILABLE:
        _require_context_provider()

    session = None
    try:
        driver = get_neo4j_driver()
        session = driver.session()
    except Exception as e:
        logger.error("Failed to create Neo4j session: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j service unavailable. Please try again later.",
        ) from e

    try:
        if context and context.is_super_admin():
            # Super-admin bypass - no tenant scoping
            return Neo4jTenantSession(
                session=session,
                tenant_id=None,
                is_bypass=True,
            )
        elif context and context.tenant_id:
            return Neo4jTenantSession(
                session=session,
                tenant_id=str(context.tenant_id),
                is_bypass=False,
            )
        else:
            # Clean up session before raising
            await session.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context required or super_admin role.",
            )
    except Exception:
        # Ensure session is closed if any error occurs
        if session is not None:
            try:
                await session.close()
            except Exception as close_error:
                logger.warning("Failed to close Neo4j session after error: %s", close_error)
        raise


def require_tenant_header_for_internal():
    """Dependency factory for internal endpoints requiring X-Tenant-ID.

    Some Layer 3 internal endpoints may need explicit tenant header validation
    for service-to-service calls. This provides a standardized way to enforce
    that without duplicating logic.

    Usage::

        @router.post("/internal/ingest")
        async def internal_ingest(
            tenant_id: str = Depends(require_tenant_header_for_internal()),
        ):
            ...
    """
    async def _check_tenant_header(request: Request) -> str:
        # CONTRACT §2.1 §2.3: All tenant identification flows through GovernanceMiddleware
        # Direct header access is prohibited. RequestContext is set by middleware.
        if not SHARED_IDENTITY_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Identity system unavailable. Ensure shared.identity is configured.",
            )

        provider = _require_context_provider()
        ctx = provider(request)
        if inspect.isawaitable(ctx):
            ctx = await ctx
        if ctx and ctx.tenant_id:
            return str(ctx.tenant_id)

        # If no context, middleware hasn't run or auth failed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context required. Ensure request passed through GovernanceMiddleware.",
        )

    return _check_tenant_header
