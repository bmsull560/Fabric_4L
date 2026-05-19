"""Layer 6 Benchmarks API Client.

Used by Layer 4 agent workflows to:
  - Fetch industry benchmarks for ROI narrative generation.
  - Retrieve dataset details for evidence backing.

The client is resilient: exceptions are caught and returned as structured
error dicts so an L6 outage never blocks narrative generation.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

DEFAULT_L6_URL = os.getenv("LAYER6_API_URL", "http://layer6-benchmarks:8006")


class Layer6BenchmarkClient:
    """HTTP client for Layer 6 Benchmarks API."""

    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = (base_url or DEFAULT_L6_URL).rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry(
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=False,
    )
    async def get_dataset(self, dataset_id: str) -> dict[str, Any]:
        """Fetch a single benchmark dataset by ID."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.base_url}/v1/benchmarks/datasets/{dataset_id}",
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as exc:
            logger.warning("L6 dataset fetch failed", dataset_id=dataset_id, error=str(exc))
            return {"success": False, "error": str(exc), "data": None}

    async def list_datasets(
        self,
        industry: str | None = None,
        segment: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """List benchmark datasets with optional filtering."""
        try:
            client = await self._get_client()
            params: dict[str, Any] = {"limit": limit}
            if industry:
                params["industry"] = industry
            if segment:
                params["segment"] = segment
            response = await client.get(
                f"{self.base_url}/v1/benchmarks/datasets",
                params=params,
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as exc:
            logger.warning("L6 dataset list failed", error=str(exc))
            return {"success": False, "error": str(exc), "data": None}

    async def get_industries(self) -> dict[str, Any]:
        """Fetch available industry list."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/v1/benchmarks/industries")
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as exc:
            logger.warning("L6 industries fetch failed", error=str(exc))
            return {"success": False, "error": str(exc), "data": None}


def get_layer6_client() -> Layer6BenchmarkClient:
    """Factory for Layer6BenchmarkClient."""
    return Layer6BenchmarkClient()
