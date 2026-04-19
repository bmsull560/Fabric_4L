"""HTTP client for resolving LLM models from Layer 4 Model Registry.

Provides async model resolution with TTL caching and fallback to environment
variables when the registry is unavailable.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx


@dataclass
class CachedModel:
    """Cached model entry with TTL."""

    model_name: str
    cached_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ttl_seconds: int = 300  # 5 minute default TTL

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now(UTC) - self.cached_at > timedelta(seconds=self.ttl_seconds)


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

    _MAX_CACHE_SIZE = 100  # Prevent unbounded cache growth

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
        self._cache_lock = asyncio.Lock()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with connection pooling."""
        if self._client is None:
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                limits=limits,
            )
        return self._client

    def _cache_key(self, tenant_id: str, provider: str) -> str:
        """Generate cache key for tenant/provider combination."""
        return f"{tenant_id}:{provider}"

    async def _get_cached(self, tenant_id: str, provider: str) -> str | None:
        """Get cached model if not expired."""
        async with self._cache_lock:
            key = self._cache_key(tenant_id, provider)
            cached = self._cache.get(key)
            if cached and not cached.is_expired():
                return cached.model_name
            return None

    async def _set_cached(self, tenant_id: str, provider: str, model_name: str) -> None:
        """Cache model resolution result with LRU eviction."""
        async with self._cache_lock:
            # Evict oldest entries if cache is at max size
            if len(self._cache) >= self._MAX_CACHE_SIZE:
                # Remove oldest 20% of entries (LRU approximation)
                entries_to_remove = max(1, self._MAX_CACHE_SIZE // 5)
                # Snapshot keys to avoid "dictionary changed size during iteration"
                oldest_keys = sorted(
                    list(self._cache.keys()),
                    key=lambda k: self._cache[k].cached_at
                )[:entries_to_remove]
                for key in oldest_keys:
                    if key in self._cache:
                        del self._cache[key]

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

    _VALID_PROVIDERS = {"openai", "anthropic"}

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
            tenant_id: Tenant ID for model lookup (required, non-empty)
            provider: Model provider (openai, anthropic)
            api_token: Optional API token for L4 authentication

        Returns:
            Model name (e.g., "gpt-4o", "claude-3-5-sonnet")

        Raises:
            ValueError: If tenant_id is empty or provider is invalid
        """
        # Input validation
        if not tenant_id or not tenant_id.strip():
            raise ValueError("tenant_id is required and cannot be empty")

        provider = provider.lower().strip()
        if provider not in self._VALID_PROVIDERS:
            raise ValueError(
                f"Invalid provider '{provider}'. Must be one of: {', '.join(self._VALID_PROVIDERS)}"
            )

        # Check cache first
        cached = await self._get_cached(tenant_id, provider)
        if cached:
            return cached

        # Attempt registry lookup with retry logic
        model = await self._fetch_with_retry(tenant_id, provider, api_token)
        if model:
            await self._set_cached(tenant_id, provider, model)
            return model

        # Fallback to environment variable
        return self._get_fallback_model(provider)

    async def _fetch_with_retry(
        self,
        tenant_id: str,
        provider: str,
        api_token: str | None = None,
        max_retries: int = 3,
    ) -> str | None:
        """Fetch active model with exponential backoff retry logic.

        Retries on transient errors (5xx, timeouts, connection errors).
        Falls back to environment variable on permanent failures.

        Args:
            tenant_id: Tenant ID
            provider: Model provider
            api_token: Optional API token
            max_retries: Maximum number of retry attempts

        Returns:
            Model name or None if not found
        """
        import asyncio
        import logging
        import random

        logger = logging.getLogger(__name__)
        last_exception: Exception | None = None

        for attempt in range(max_retries):
            try:
                return await self._fetch_from_registry(tenant_id, provider, api_token)
            except httpx.HTTPStatusError as exc:
                # Retry on 5xx server errors, fail fast on 4xx client errors
                if exc.response.status_code >= 500:
                    last_exception = exc
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Registry request failed (attempt {attempt + 1}/{max_retries}): "
                        f"{exc}. Retrying in {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # 4xx errors are client errors, don't retry
                    logger.warning(f"Registry request failed with client error: {exc}")
                    break
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                # Network/transient errors should be retried
                last_exception = exc
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(
                    f"Registry connection error (attempt {attempt + 1}/{max_retries}): "
                    f"{exc}. Retrying in {wait_time:.1f}s..."
                )
                await asyncio.sleep(wait_time)

        # All retries exhausted or non-retryable error
        logger.error(
            f"Failed to resolve model from registry for tenant {tenant_id} after "
            f"{max_retries} attempts: {last_exception}. Falling back to environment variable."
        )
        return None

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
            return None  # pragma: no cover

    async def close(self) -> None:
        """Close HTTP client connections and clear cache."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._cache.clear()  # Prevent stale data across client lifecycles

    async def __aenter__(self) -> ModelRegistryClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
