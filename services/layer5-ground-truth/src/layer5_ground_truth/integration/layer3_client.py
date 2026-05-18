"""
Layer 3 Knowledge Graph integration client for Layer 5.

Responsibilities:
  - Sync approved TruthObjects to the Layer 3 KG as :GroundTruth nodes
  - Link GroundTruth nodes to existing :Capability / :Outcome / :ValueDriver nodes
  - Query Layer 3 for entity context when creating truth objects
  - Handle connection failures gracefully (Layer 5 is authoritative; KG sync is best-effort)

Layer 3 API base URL is configured via LAYER3_BASE_URL env var (default: http://localhost:8003).
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

import httpx

from metrics.prometheus_metrics import get_metrics

from ..config import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Node type mapping
# ---------------------------------------------------------------------------

# Maps Layer 5 ClaimType → Layer 3 node label for relationship creation
CLAIM_TYPE_TO_KG_LABEL: dict[str, str] = {
    "cost_savings_baseline": "ValueDriver",
    "revenue_impact": "ValueDriver",
    "efficiency_gain": "ValueDriver",
    "risk_reduction": "ValueDriver",
    "compliance_requirement": "Outcome",
    "customer_outcome": "Outcome",
    "technical_capability": "Capability",
    "market_benchmark": "ValueDriver",
    "persona_pain_point": "Persona",
    "value_driver_metric": "ValueDriver",
    "other": "Entity",
}


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class Layer3Client:
    """
    Async HTTP client for Layer 3 Knowledge Graph API.

    All methods return None on failure and log a warning — Layer 5 must
    remain operational even when Layer 3 is unavailable.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._base_url = self._settings.layer3_base_url.rstrip("/")
        self._timeout = self._settings.layer3_timeout_seconds
        self._headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._settings.layer3_api_key:
            self._headers["Authorization"] = f"Bearer {self._settings.layer3_api_key}"
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Return (or lazily create) the persistent HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                headers=self._headers,
            )
        return self._client

    async def close(self) -> None:
        """Close the persistent HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        """Return True if Layer 3 is reachable."""
        try:
            client = self._get_client()
            resp = await client.get(
                f"{self._base_url}/health", headers=self._headers
            )
            return resp.status_code == 200
        except Exception as exc:
            logger.debug("Layer 3 ping failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Sync TruthObject → Knowledge Graph
    # ------------------------------------------------------------------

    async def sync_truth_object(
        self,
        truth_object_id: UUID,
        tenant_id: UUID,
        claim: str,
        claim_type: str,
        confidence: float,
        status: str,
        maturity_level: int,
        value: dict | None = None,
        applies_to: dict | None = None,
        source_count: int = 0,
    ) -> str | None:
        """
        Create or update a :GroundTruth node in the Layer 3 Knowledge Graph.

        Returns the KG node ID on success, None on failure.

        The node is created with the Cypher pattern:
          MERGE (g:GroundTruth {truth_object_id: $id, tenant_id: $org_id})
          SET g += $properties
          RETURN g.id
        """
        if not self._settings.layer3_sync_enabled:
            metrics = get_metrics()
            if metrics:
                metrics.increment_kg_sync_outcome(
                    sync_status="disabled", transition=f"{status}->kg_sync"
                )
            logger.debug(
                "Layer 3 sync disabled — skipping sync for %s", truth_object_id
            )
            return None

        payload = {
            "node_type": "GroundTruth",
            "properties": {
                "truth_object_id": str(truth_object_id),
                "tenant_id": str(tenant_id),
                "claim": claim,
                "claim_type": claim_type,
                "confidence": confidence,
                "status": status,
                "maturity_level": maturity_level,
                "source_count": source_count,
                "value": value,
                "applies_to": applies_to,
            },
            "merge_keys": ["truth_object_id", "tenant_id"],
        }

        # Retry with exponential backoff for transient failures
        max_retries = 3
        for attempt in range(max_retries):
            try:
                client = self._get_client()
                resp = await client.post(
                    f"{self._base_url}/api/v1/nodes",
                    json=payload,
                    headers=self._headers,
                )
                resp.raise_for_status()
                data = resp.json()
                node_id: str = data.get("id") or data.get("node_id", "")
                logger.info(
                    "Synced TruthObject %s to Layer 3 KG as node %s",
                    truth_object_id,
                    node_id,
                )
                metrics = get_metrics()
                if metrics:
                    metrics.increment_kg_sync(status="success")
                    metrics.increment_kg_sync_outcome(
                        sync_status="success", transition=f"{status}->kg_sync"
                    )
                logger.info(
                    "kg sync outcome",
                    extra={
                        "request_id": None,
                        "tenant_id": str(tenant_id),
                        "truth_object_id": str(truth_object_id),
                        "transition": f"{status}->kg_sync",
                        "sync_status": "success",
                    },
                )
                return node_id
            except httpx.HTTPStatusError as exc:
                # Don't retry 4xx errors (client errors)
                if 400 <= exc.response.status_code < 500:
                    metrics = get_metrics()
                    if metrics:
                        metrics.increment_kg_sync(status="client_error")
                        metrics.increment_kg_sync_outcome(
                            sync_status="client_error",
                            transition=f"{status}->kg_sync",
                        )
                    logger.warning(
                        "Layer 3 sync failed for TruthObject %s: HTTP %d — %s",
                        truth_object_id,
                        exc.response.status_code,
                        exc.response.text[:200],
                    )
                    return None
                # Retry 5xx errors on attempts before max
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # 1s, 2s, 4s
                    logger.warning(
                        "Layer 3 sync attempt %d/%d failed with HTTP %d, retrying in %ds",
                        attempt + 1,
                        max_retries,
                        exc.response.status_code,
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    continue
                # Final attempt failed
                logger.warning(
                    "Layer 3 sync failed for TruthObject %s after %d attempts: HTTP %d",
                    truth_object_id,
                    max_retries,
                    exc.response.status_code,
                )
                metrics = get_metrics()
                if metrics:
                    metrics.increment_kg_sync(status="server_error")
                    metrics.increment_kg_sync_outcome(
                        sync_status="server_error",
                        transition=f"{status}->kg_sync",
                    )
                return None
            except Exception as exc:
                # Retry on connection errors
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        "Layer 3 sync attempt %d/%d failed (%s), retrying in %ds",
                        attempt + 1,
                        max_retries,
                        exc,
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    continue
                # Final attempt failed
                logger.warning(
                    "Layer 3 sync failed for TruthObject %s after %d attempts: %s",
                    truth_object_id,
                    max_retries,
                    exc,
                )
                metrics = get_metrics()
                if metrics:
                    metrics.increment_kg_sync(status="exception")
                    metrics.increment_kg_sync_outcome(
                        sync_status="exception", transition=f"{status}->kg_sync"
                    )
                logger.warning(
                    "kg sync outcome",
                    extra={
                        "request_id": None,
                        "tenant_id": str(tenant_id),
                        "truth_object_id": str(truth_object_id),
                        "transition": f"{status}->kg_sync",
                        "sync_status": "failed",
                    },
                )
                return None
        return None

    # ------------------------------------------------------------------
    # Link GroundTruth node to existing KG entities
    # ------------------------------------------------------------------

    async def link_to_entity(
        self,
        kg_node_id: str,
        target_entity_id: str,
        relationship_type: str = "GROUNDS",
        properties: dict | None = None,
    ) -> bool:
        """
        Create a relationship between a GroundTruth node and an existing KG entity.

        Default relationship: (GroundTruth)-[:GROUNDS]->(Entity)

        Returns True on success.
        """
        if not self._settings.layer3_sync_enabled:
            return False

        payload = {
            "from_node_id": kg_node_id,
            "to_node_id": target_entity_id,
            "relationship_type": relationship_type,
            "properties": properties or {},
        }

        # Retry with exponential backoff for transient failures
        max_retries = 3
        for attempt in range(max_retries):
            try:
                client = self._get_client()
                resp = await client.post(
                    f"{self._base_url}/api/v1/relationships",
                    json=payload,
                    headers=self._headers,
                )
                resp.raise_for_status()
                logger.info(
                    "Linked KG node %s -[%s]-> %s",
                    kg_node_id,
                    relationship_type,
                    target_entity_id,
                )
                return True
            except httpx.HTTPStatusError as exc:
                # Don't retry 4xx errors
                if 400 <= exc.response.status_code < 500:
                    logger.warning(
                        "Layer 3 link failed: %s -[%s]-> %s: HTTP %d",
                        kg_node_id,
                        relationship_type,
                        target_entity_id,
                        exc.response.status_code,
                    )
                    return False
                # Retry 5xx on non-final attempts
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    continue
                logger.warning(
                    "Layer 3 link failed after %d attempts: %s -[%s]-> %s: HTTP %d",
                    max_retries,
                    kg_node_id,
                    relationship_type,
                    target_entity_id,
                    exc.response.status_code,
                )
                return False
            except Exception as exc:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    continue
                logger.warning(
                    "Layer 3 link failed after %d attempts: %s -[%s]-> %s: %s",
                    max_retries,
                    kg_node_id,
                    relationship_type,
                    target_entity_id,
                    exc,
                )
                return False

    # ------------------------------------------------------------------
    # Query Layer 3 for entity context
    # ------------------------------------------------------------------

    async def get_entity_context(
        self,
        entity_id: str,
        tenant_id: UUID,
    ) -> dict[str, Any] | None:
        """
        Fetch entity metadata from Layer 3 to enrich a TruthObject.

        Returns the entity dict or None if not found / unavailable.
        """
        try:
            client = self._get_client()
            resp = await client.get(
                f"{self._base_url}/api/v1/entities/{entity_id}",
                params={"tenant_id": str(tenant_id)},
                headers=self._headers,
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.debug(
                "Layer 3 entity context fetch failed for %s: %s", entity_id, exc
            )
            return None

    # ------------------------------------------------------------------
    # Bulk sync helper (called by background task)
    # ------------------------------------------------------------------

    async def bulk_sync_approved(
        self,
        truth_objects: list[dict[str, Any]],
    ) -> dict[str, str | None]:
        """
        Sync a list of approved TruthObjects to Layer 3.

        Returns a mapping of truth_object_id → kg_node_id (or None on failure).
        """
        results: dict[str, str | None] = {}
        for obj in truth_objects:
            node_id = await self.sync_truth_object(
                truth_object_id=obj["id"],
                tenant_id=obj["tenant_id"],
                claim=obj["claim"],
                claim_type=obj["claim_type"],
                confidence=obj["confidence"],
                status=obj["status"],
                maturity_level=obj["maturity_level"],
                value=obj.get("value"),
                applies_to=obj.get("applies_to"),
                source_count=obj.get("source_count", 0),
            )
            results[str(obj["id"])] = node_id
        return results


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_client: Layer3Client | None = None


def get_layer3_client() -> Layer3Client:
    """Return the shared Layer3Client singleton."""
    global _client
    if _client is None:
        _client = Layer3Client()
    return _client
