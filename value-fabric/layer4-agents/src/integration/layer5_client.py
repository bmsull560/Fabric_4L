"""Layer 5 Ground Truth API Client.

Used by Layer 4 agent workflows to:
  - Sync approved TruthObjects to the Layer 3 Knowledge Graph after a
    business case is generated (POST /truths/sync-kg).
  - Submit new TruthObjects extracted during workflow execution.
  - Query existing TruthObjects for context enrichment.

The client is intentionally resilient: every public method catches all
exceptions and returns a structured error dict rather than raising, so
a Layer 5 outage never blocks a business case generation.
"""

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

_DEFAULT_BASE_URL = os.getenv("LAYER5_GROUND_TRUTH_URL", "http://layer5-ground-truth:8005")
_DEFAULT_TIMEOUT = 30.0

# Retry configuration: 3 attempts with exponential backoff
_RETRY_WAIT_MIN = 1  # seconds
_RETRY_WAIT_MAX = 10  # seconds
_RETRY_STOP_AFTER = 3


class Layer5GroundTruthClient:
    """Async HTTP client for the Layer 5 Ground Truth service.

    Example::

        client = Layer5GroundTruthClient(
            base_url="http://layer5-ground-truth:8005",
            service_token="<jwt-signed-by-shared-secret>",
        )

        # After business case generation completes:
        result = await client.sync_approved_truths(
            organization_id="org-uuid-here"
        )
        logger.info("Synced %d truths to KG", result.get("synced", 0))
    """

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        service_token: str | None = None,
        tenant_id: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        """Initialise the client.

        Args:
            base_url: Layer 5 service base URL.
            service_token: Bearer JWT for service-to-service auth.  When
                provided it is sent as ``Authorization: Bearer <token>``.
            tenant_id: Fallback tenant UUID sent as ``X-Tenant-ID`` when no
                JWT is available (dev / test only).
            timeout: Per-request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if service_token:
            headers["Authorization"] = f"Bearer {service_token}"
        elif tenant_id:
            headers["X-Tenant-ID"] = tenant_id

        # Connection pooling with explicit limits for boundary resilience
        limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
            limits=limits,
        )

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        """Return True if Layer 5 is reachable and healthy."""
        try:
            resp = await self._client.get("/api/v1/health")
            return resp.status_code == 200
        except Exception as exc:
            logger.debug("Layer 5 ping failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Core: sync approved truths to KG
    # ------------------------------------------------------------------

    @retry(
        wait=wait_exponential(min=_RETRY_WAIT_MIN, max=_RETRY_WAIT_MAX),
        stop=stop_after_attempt(_RETRY_STOP_AFTER),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
        reraise=False,
    )
    async def sync_approved_truths(
        self,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        """Trigger a bulk sync of all APPROVED TruthObjects to Layer 3 KG.

        This is the primary integration point called at the end of the
        Business Case Generator workflow.

        Args:
            organization_id: Tenant UUID.  Required when the client was
                initialised without a JWT (i.e. using the query-param
                fallback path).

        Returns:
            Dict with keys ``synced``, ``failed``, ``total_pending``,
            or ``error`` on failure.
        """
        params: dict[str, str] = {}
        if organization_id:
            params["organization_id"] = str(organization_id)

        try:
            resp = await self._client.post("/api/v1/truths/sync-kg", params=params)
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                "Layer 5 sync-kg: synced=%s failed=%s total_pending=%s",
                data.get("synced"),
                data.get("failed"),
                data.get("total_pending"),
            )
            return data
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Layer 5 sync-kg returned HTTP %s: %s",
                exc.response.status_code,
                exc.response.text[:200],
            )
            return {
                "error": f"HTTP {exc.response.status_code}",
                "detail": exc.response.text[:200],
                "synced": 0,
                "failed": 0,
            }
        except Exception as exc:
            logger.warning("Layer 5 sync-kg failed (non-blocking): %s", exc)
            return {"error": str(exc), "synced": 0, "failed": 0}

    # ------------------------------------------------------------------
    # Submit a new TruthObject
    # ------------------------------------------------------------------

    @retry(
        wait=wait_exponential(min=_RETRY_WAIT_MIN, max=_RETRY_WAIT_MAX),
        stop=stop_after_attempt(_RETRY_STOP_AFTER),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
        reraise=False,
    )
    async def submit_truth(
        self,
        claim: str,
        claim_type: str,
        confidence: float,
        organization_id: str | None = None,
        value: float | None = None,
        applies_to: dict[str, Any] | None = None,
        sources: list[dict[str, Any]] | None = None,
        extraction_job_id: str | None = None,
        extraction_model: str | None = None,
        raw_extraction_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new TruthObject in Layer 5.

        Args:
            claim: Human-readable factual statement.
            claim_type: One of ``capability``, ``outcome``, ``metric``,
                ``benchmark``, ``roi_assumption``, ``competitive``.
            confidence: 0.0–1.0 extraction confidence.
            organization_id: Tenant UUID (query-param fallback).
            value: Optional numeric value associated with the claim.
            applies_to: Dict with optional keys ``opportunity_id``,
                ``account_id``, ``domain``, ``use_case_id``.
            sources: List of source dicts (``url``, ``source_type``,
                ``excerpt``, ``confidence``).
            extraction_job_id: Layer 2 job ID that produced this claim.
            extraction_model: Model name used for extraction.
            raw_extraction_data: Raw LLM output for audit purposes.

        Returns:
            Created TruthObject dict, or ``{"error": ...}`` on failure.
        """
        body: dict[str, Any] = {
            "claim": claim,
            "claim_type": claim_type,
            "confidence": confidence,
        }
        if value is not None:
            body["value"] = value
        if applies_to:
            body["applies_to"] = applies_to
        if sources:
            body["sources"] = sources
        if extraction_job_id:
            body["extraction_job_id"] = extraction_job_id
        if extraction_model:
            body["extraction_model"] = extraction_model
        if raw_extraction_data:
            body["raw_extraction_data"] = raw_extraction_data

        params: dict[str, str] = {}
        if organization_id:
            params["organization_id"] = str(organization_id)

        try:
            resp = await self._client.post("/api/v1/truths", json=body, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Layer 5 submit_truth HTTP %s: %s",
                exc.response.status_code,
                exc.response.text[:200],
            )
            return {
                "error": f"HTTP {exc.response.status_code}",
                "detail": exc.response.text[:200],
            }
        except Exception as exc:
            logger.warning("Layer 5 submit_truth failed: %s", exc)
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # Query TruthObjects
    # ------------------------------------------------------------------

    async def list_truths(
        self,
        organization_id: str | None = None,
        status: str | None = None,
        claim_type: str | None = None,
        min_maturity: int | None = None,
        min_confidence: float | None = None,
        applies_to_opportunity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List TruthObjects with optional filters.

        Returns:
            Dict with ``items``, ``total``, ``limit``, ``offset``,
            ``has_more``, or ``{"error": ...}`` on failure.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if organization_id:
            params["organization_id"] = str(organization_id)
        if status:
            params["status"] = status
        if claim_type:
            params["claim_type"] = claim_type
        if min_maturity is not None:
            params["min_maturity"] = min_maturity
        if min_confidence is not None:
            params["min_confidence"] = min_confidence
        if applies_to_opportunity:
            params["applies_to_opportunity"] = applies_to_opportunity

        try:
            resp = await self._client.get("/api/v1/truths", params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("Layer 5 list_truths failed: %s", exc)
            return {"error": str(exc), "items": [], "total": 0}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


# ---------------------------------------------------------------------------
# Module-level singleton factory
# ---------------------------------------------------------------------------

_client_instance: Layer5GroundTruthClient | None = None


def get_layer5_client(
    base_url: str | None = None,
    service_token: str | None = None,
    tenant_id: str | None = None,
) -> Layer5GroundTruthClient:
    """Return a module-level singleton Layer5GroundTruthClient.

    The singleton is created on first call.  Pass explicit arguments to
    override the environment-variable defaults (useful in tests).
    """
    global _client_instance
    if _client_instance is None or base_url or service_token or tenant_id:
        _client_instance = Layer5GroundTruthClient(
            base_url=base_url or _DEFAULT_BASE_URL,
            service_token=service_token,
            tenant_id=tenant_id,
        )
    return _client_instance
