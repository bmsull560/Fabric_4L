"""Layer 3 Knowledge Graph client with tenant propagation (Task 2.3).

Provides async HTTP client for Layer 3 Knowledge Graph API with automatic
tenant context injection for all queries.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

TENANT_ID_HEADER = "X-Tenant-ID"


class Layer3ClientError(Exception):
    """Raised when Layer 3 API call fails."""

    pass


class Layer3Client:
    """Async client for Layer 3 Knowledge Graph API with tenant propagation.

    All methods automatically include tenant_id as X-Tenant-ID header
    to ensure RLS policies are enforced at Layer 3.

    Example:
        client = Layer3Client("http://layer3:8000")

        # Query with tenant context
        result = await client.query_graph(
            tenant_id="tenant-123",
            query="MATCH (n:Account) RETURN n LIMIT 10"
        )
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        tenant_id: str | None = None,
        max_retries: int = 3,
    ):
        """Initialize Layer 3 client.

        Args:
            base_url: Layer 3 API base URL
            timeout: Request timeout in seconds
            tenant_id: Default tenant ID for all requests
            max_retries: Max retry attempts for transient failures
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._default_tenant_id = tenant_id
        self._max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    def _get_headers(self, tenant_id: str | None = None) -> dict[str, str]:
        """Build request headers with tenant context.

        Args:
            tenant_id: Tenant ID to include in headers (uses default if None)

        Returns:
            Headers dict with X-Tenant-ID if tenant_id available
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        effective_tenant = tenant_id or self._default_tenant_id
        if effective_tenant:
            headers[TENANT_ID_HEADER] = effective_tenant

        return headers

    def _get_effective_tenant(self, tenant_id: str | None) -> str:
        """Get effective tenant ID or raise error if not available.

        Args:
            tenant_id: Optional tenant ID override

        Returns:
            Effective tenant ID

        Raises:
            Layer3ClientError: If no tenant ID available
        """
        effective = tenant_id or self._default_tenant_id
        if not effective:
            raise Layer3ClientError(
                "Tenant ID required. Provide tenant_id parameter or set default in constructor."
            )
        return effective

    async def _make_request(
        self,
        method: str,
        url: str,
        tenant_id: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        allow_404: bool = False,
    ) -> dict[str, Any] | None:
        """Make HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            tenant_id: Tenant ID for headers
            json: Optional JSON body
            params: Optional query params
            allow_404: If True, return None on 404 instead of raising

        Returns:
            Response JSON or None if 404 and allow_404=True

        Raises:
            Layer3ClientError: On request failure
        """
        client = await self._get_client()
        headers = self._get_headers(tenant_id)

        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                    params=params,
                )

                if response.status_code == 404 and allow_404:
                    return None

                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Don't retry 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    raise Layer3ClientError(
                        f"Request failed: HTTP {e.response.status_code}"
                    )
                last_error = e
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                # Retry transient network errors
                last_error = e
            except Exception as e:
                raise Layer3ClientError(f"Request failed: {e}")

        raise Layer3ClientError(f"Request failed after {self._max_retries} attempts: {last_error}")

    async def query_graph(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute Cypher query against knowledge graph.

        Args:
            query: Cypher query string
            parameters: Query parameters
            tenant_id: Tenant ID for RLS (uses default if None)

        Returns:
            Query results

        Raises:
            Layer3ClientError: If query fails
        """
        effective_tenant = self._get_effective_tenant(tenant_id)
        url = f"{self.base_url}/v1/graph/query"
        payload = {
            "query": query,
            "parameters": parameters or {},
        }
        return await self._make_request("POST", url, effective_tenant, json=payload)

    async def get_subgraph(
        self,
        center_entity_id: str,
        depth: int = 2,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Get subgraph centered on an entity.

        Args:
            center_entity_id: Entity to center subgraph on
            depth: Traversal depth (1-3)
            tenant_id: Tenant ID for RLS (uses default if None)

        Returns:
            Subgraph with nodes and edges
        """
        effective_tenant = self._get_effective_tenant(tenant_id)
        url = f"{self.base_url}/v1/graph/subgraph"
        params = {
            "center_entity_id": center_entity_id,
            "depth": depth,
        }
        return await self._make_request("GET", url, effective_tenant, params=params)

    async def semantic_search(
        self,
        query: str,
        entity_types: list[str] | None = None,
        limit: int = 10,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Perform semantic search across entities.

        Args:
            query: Search query text
            entity_types: Optional filter by entity types
            limit: Maximum results
            tenant_id: Tenant ID for RLS (uses default if None)

        Returns:
            Search results
        """
        effective_tenant = self._get_effective_tenant(tenant_id)
        url = f"{self.base_url}/v1/entities/search"
        payload: dict[str, Any] = {
            "query": query,
            "limit": limit,
        }
        if entity_types:
            payload["entity_types"] = entity_types

        result = await self._make_request("POST", url, effective_tenant, json=payload)
        return result or {}

    async def get_entity(
        self,
        entity_id: str,
        tenant_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Get entity by ID.

        Args:
            entity_id: Entity identifier
            tenant_id: Tenant ID for RLS (uses default if None)

        Returns:
            Entity data or None if not found
        """
        effective_tenant = self._get_effective_tenant(tenant_id)
        url = f"{self.base_url}/v1/entities/{entity_id}"

        return await self._make_request("GET", url, effective_tenant, allow_404=True)

    async def close(self) -> None:
        """Close HTTP client and release resources."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> Layer3Client:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
