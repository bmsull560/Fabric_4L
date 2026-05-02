"""Tenant-aware Neo4j dependencies with query validation (Phase 4).

Provides secure Neo4j session injection with:
1. Automatic tenant_id extraction from RequestContext
2. Query validation before execution (blocks unscoped reads)
3. Defense-in-depth for multi-tenant data isolation
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import Depends, HTTPException, Request, status

from src.security import QueryValidator, UnscopedQueryError

if TYPE_CHECKING:
    from neo4j import AsyncSession

try:
    from shared.identity.context import RequestContext
    from shared.identity.dependencies import get_request_context
    IDENTITY_AVAILABLE = True
except ImportError:
    IDENTITY_AVAILABLE = False
    RequestContext = None  # type: ignore


logger = logging.getLogger(__name__)

# Query validator instance (singleton)
_query_validator: QueryValidator | None = None


def get_query_validator() -> QueryValidator:
    """Get singleton query validator instance."""
    global _query_validator
    if _query_validator is None:
        _query_validator = QueryValidator(fail_closed=True)
    return _query_validator


class Neo4jTenantSessionSecured:
    """Tenant-scoped Neo4j session with query validation.
    
    This class wraps Neo4j sessions to provide defense-in-depth
    for multi-tenant query isolation. It:
    
    1. Validates all Cypher queries for tenant_id scoping
    2. Injects tenant_id into query parameters automatically
    3. Blocks unscoped Entity MATCH clauses that could leak data
    
    Example:
        >>> async with Neo4jTenantSessionSecured(driver, tenant_id) as session:
        ...     # Valid query - passes validation
        ...     result = await session.run(
        ...         "MATCH (e:Entity {id: $id, tenant_id: $tenant_id}) RETURN e",
        ...         id="abc"
        ...     )
        ...     
        ...     # Invalid query - raises UnscopedQueryError
        ...     result = await session.run(
        ...         "MATCH (e:Entity {id: $id}) RETURN e",  # Missing tenant_id!
        ...         id="abc"
        ...     )
    """
    
    def __init__(
        self,
        driver,
        tenant_id: str,
        *,
        strict_validation: bool = True,
    ):
        """Initialize secured tenant session.
        
        Args:
            driver: Neo4j async driver
            tenant_id: Tenant ID for query scoping
            strict_validation: If True, block all unscoped queries
        """
        self._driver = driver
        self._tenant_id = tenant_id
        self._strict = strict_validation
        self._validator = get_query_validator()
        self._session: AsyncSession | None = None
    
    async def __aenter__(self) -> Neo4jTenantSessionSecured:
        """Enter async context and create underlying session."""
        self._session = self._driver.session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and cleanup session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def run(self, query: str, parameters: dict | None = None, **kwargs) -> Any:
        """Execute query with validation and tenant scoping.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            **kwargs: Additional parameters
            
        Returns:
            Query result
            
        Raises:
            UnscopedQueryError: If query fails tenant isolation validation
            HTTPException: 500 if session not initialized
        """
        if not self._session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Neo4j session not initialized"
            )
        
        # Validate query for tenant scoping
        if self._strict:
            try:
                findings = self._validator.validate(query, query_name="neo4j.run")
                if findings:
                    errors = [f for f in findings if f.severity.value == "error"]
                    if errors:
                        raise UnscopedQueryError(
                            f"Query validation failed: {errors[0].message}"
                        )
            except UnscopedQueryError:
                logger.warning(
                    f"Blocked unscoped query for tenant {self._tenant_id}: {query[:100]}..."
                )
                raise
        
        # Inject tenant_id into parameters
        params = parameters or {}
        params.update(kwargs)
        
        if "tenant_id" not in params:
            params["tenant_id"] = self._tenant_id
        
        return await self._session.run(query, params)


async def get_neo4j_secured(
    request: Request,
    context: RequestContext = Depends(get_request_context),
) -> Neo4jTenantSessionSecured:
    """FastAPI dependency for secured, tenant-scoped Neo4j sessions.
    
    This is the RECOMMENDED dependency for all endpoints that query Neo4j.
    It provides automatic tenant extraction and query validation.
    
    Usage:
        @router.get("/entities/{id}")
        async def get_entity(
            id: str,
            neo4j: Neo4jTenantSessionSecured = Depends(get_neo4j_secured)
        ):
            async with neo4j:
                result = await neo4j.run(
                    "MATCH (e:Entity {id: $id, tenant_id: $tenant_id}) RETURN e",
                    id=id
                )
                ...
    
    Args:
        request: FastAPI request object
        context: Request context with tenant_id
        
    Returns:
        Configured Neo4jTenantSessionSecured instance
        
    Raises:
        HTTPException: 400 if tenant context missing, 503 if Neo4j unavailable
    """
    if not IDENTITY_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity service unavailable"
        )
    
    if not context or not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    driver = getattr(request.app.state, "neo4j_driver", None)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j service unavailable"
        )
    
    return Neo4jTenantSessionSecured(
        driver=driver,
        tenant_id=str(context.tenant_id),
        strict_validation=True
    )


async def get_neo4j_with_validation(
    request: Request,
    context: RequestContext = Depends(get_request_context),
) -> Neo4jTenantSessionSecured:
    """Alias for get_neo4j_secured - explicit validation naming.
    
    Use this dependency when you want to emphasize that query validation
    is being applied for security compliance.
    """
    return await get_neo4j_secured(request, context)


# Backward-compatible alias
Neo4jTenantValidatedSession = Neo4jTenantSessionSecured
