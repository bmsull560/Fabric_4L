"""HTTP client for resolving LLM models from Layer 4 Model Registry.

Provides async model resolution with TTL caching and fallback to environment
variables when the registry is unavailable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import httpx


@dataclass
class CachedModel:
    """Cached model entry with TTL."""

    model_name: str
    cached_at: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: int = 300  # 5 minute default TTL

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.utcnow() - self.cached_at > timedelta(seconds=self.ttl_seconds)


class ModelRegistryClient:
    """Async HTTP client for Layer 4 Model Registry.

    Resolves the active production LLM model for a tenant with caching
    to minimize registry calls. Falls back to environment variables
    when registry is unavailable.

    Example:
        client = ModelRegistryClient(base_url="http://layer4:8000")
        model = await client.resolve_model(
            tenant_id="tenant-123",
            provider="openai",
            api_token="secret-token"
        )
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 5.0,
        cache_ttl_seconds: int = 300,
    ):
        """Initialize registry client.

        Args:
            base_url: L4 API base URL (defaults to L4_API_URL env var)
            timeout: Request timeout in seconds
            cache_ttl_seconds: Cache TTL for model resolution
        """
        self.base_url = base_url or os.getenv("L4_API_URL", "http://layer4-agents:8000")
        self.timeout = timeout
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, CachedModel] = {}
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    def _cache_key(self, tenant_id: str, provider: str) -> str:
        """Generate cache key for tenant/provider combination."""
        return f"{tenant_id}:{provider}"

    def _get_cached(self, tenant_id: str, provider: str) -> str | None:
        """Get cached model if not expired."""
        key = self._cache_key(tenant_id, provider)
        cached = self._cache.get(key)
        if cached and not cached.is_expired():
            return cached.model_name
        return None

    def _set_cached(self, tenant_id: str, provider: str, model_name: str) -> None:
        """Cache model resolution result."""
        key = self._cache_key(tenant_id, provider)
        self._cache[key] = CachedModel(
            model_name=model_name,
            ttl_seconds=self.cache_ttl_seconds,
        )

    def _get_fallback_model(self, provider: str) -> str:
        """Get fallback model from environment variables."""
        if provider == "openai":
            return os.getenv("L2_OPENAI_MODEL", "gpt-4o")
        elif provider == "anthropic":
            return os.getenv("L2_ANTHROPIC_MODEL", "claude-3-5-sonnet")
        else:
            return os.getenv("LLM_MODEL", "gpt-4o")

    async def resolve_model(
        self,
        tenant_id: str,
        provider: str = "openai",
        api_token: str | None = None,
    ) -> str:
        """Resolve active production model from registry.

        Uses cached value if available and not expired. Falls back to
        environment variables on any failure.

        Args:
            tenant_id: Tenant ID for model lookup
            provider: Model provider (openai, anthropic)
            api_token: Optional API token for L4 authentication

        Returns:
            Model name (e.g., "gpt-4o", "claude-3-5-sonnet")
        """
        # Check cache first
        cached = self._get_cached(tenant_id, provider)
        if cached:
            return cached

        # Attempt registry lookup
        try:
            model = await self._fetch_from_registry(tenant_id, provider, api_token)
            if model:
                self._set_cached(tenant_id, provider, model)
                return model
        except Exception as exc:
            # Log warning but don't fail - fall back to env var
            import logging

            logging.getLogger(__name__).warning(
                f"Failed to resolve model from registry for tenant {tenant_id}: {exc}. "
                f"Falling back to environment variable."
            )

        # Fallback to environment variable
        return self._get_fallback_model(provider)

    async def _fetch_from_registry(
        self,
        tenant_id: str,
        provider: str,
        api_token: str | None = None,
    ) -> str | None:
        """Fetch active model from L4 registry API.

        Args:
            tenant_id: Tenant ID
            provider: Model provider
            api_token: Optional API token

        Returns:
            Model name or None if not found
        """
        client = await self._get_client()

        headers: dict[str, str] = {"X-Tenant-ID": tenant_id}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"

        response = await client.get(
            "/v1/models/active",
            params={"provider": provider},
            headers=headers,
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("model_name")
        elif response.status_code == 404:
            # No active production model found
            return None
        else:
            response.raise_for_status()
            return None

    async def close(self) -> None:
        """Close HTTP client connections."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> ModelRegistryClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
