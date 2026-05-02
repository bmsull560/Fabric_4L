"""Layer 3 Knowledge Graph client for Layer 2 extraction pipeline.

Provides integration between Layer 2 (Extraction) and Layer 3 (Knowledge Graph),
enabling extraction results to be ingested into Neo4j via the Layer 3 API.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

from layer2_extraction.models import ExtractionResult
from layer2_extraction.output.rdf_generator import generate_rdf
from shared.models.typed_dict import TypedDictModel


class Layer3KnowledgeClient_detailed_health_checkResult(TypedDictModel):
    error: Any
    status: str

class Layer3KnowledgeClient_graph_rag_queryResult(TypedDictModel):
    entities: list[Any]
    error: Any
    relationships: list[Any]

logger = logging.getLogger(__name__)


@dataclass
class IngestionResponse:
    """Response from Layer 3 ingestion API."""

    success: bool
    ingestion_id: str
    entities_loaded: int
    relationships_loaded: int
    message: str
    error: str | None = None


@dataclass
class IngestionStatus:
    """Status of an ingestion job."""

    ingestion_id: str
    status: str  # pending, processing, completed, failed
    progress_percent: float
    entities_processed: int
    entities_total: int
    error_message: str | None = None


class Layer3KnowledgeClient:
    """Client for pushing extraction results to Layer 3 Knowledge Graph.

    This client handles:
    - Converting extraction results to RDF
    - Calling Layer 3 ingest API
    - Batching for large extractions
    - Retry logic with exponential backoff
    - Health checking Layer 3 availability

    Example:
        client = Layer3KnowledgeClient(
            base_url="http://localhost:8001",
            api_key="optional-api-key"
        )

        # Check health
        if await client.health_check():
            # Ingest extraction results
            response = await client.ingest_extraction_result(
                extraction_result=result,
                source_url="https://example.com/doc",
                extraction_job_id="job_123"
            )
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        batch_size: int = 100,
    ):
        """Initialize Layer 3 client.

        Args:
            base_url: Layer 3 API base URL (or LAYER3_API_URL env var)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            batch_size: Number of entities to process per batch
        """
        self.base_url = base_url or os.getenv("LAYER3_API_URL", "http://localhost:8001")
        self.api_key = api_key or os.getenv("LAYER3_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries
        self.batch_size = batch_size

        # Setup HTTP client
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(timeout, connect=10.0),
        )

        logger.info(f"Layer3KnowledgeClient initialized for {self.base_url}")

    async def close(self) -> None:
        """Close HTTP client connection."""
        await self._client.aclose()

    async def health_check(self) -> bool:
        """Check if Layer 3 API and Neo4j are healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self._client.get("/health", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                logger.debug(f"Layer 3 health status: {status}")
                return status in ("healthy", "degraded")
            return False
        except Exception as e:
            logger.warning(f"Layer 3 health check failed: {e}")
            return False

    async def detailed_health_check(self) -> dict[str, Any]:
        """Get detailed health information from Layer 3.

        Returns:
            Health check response data
        """
        try:
            response = await self._client.get("/health/detailed", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Detailed health check failed: {e}")
            return Layer3KnowledgeClient_detailed_health_checkResult.model_validate({"status": "error", "error": str(e)})

    async def ingest_extraction_result(
        self,
        extraction_result: ExtractionResult,
        source_url: str,
        extraction_job_id: str,
        relationships: list[Any] | None = None,
        batch_size: int | None = None,
    ) -> IngestionResponse:
        """Ingest extraction results into Layer 3 Knowledge Graph.

        This method:
        1. Converts extraction result to RDF
        2. Calls Layer 3 ingest API
        3. Returns ingestion statistics

        Args:
            extraction_result: Entities and relationships from extraction
            source_url: Source document URL
            extraction_job_id: Job ID for tracking
            relationships: Optional relationship list for RDF generation
            batch_size: Override default batch size

        Returns:
            IngestionResponse with status and statistics
        """
        batch_size = batch_size or self.batch_size

        try:
            # Convert to RDF
            logger.info(f"Converting extraction {extraction_job_id} to RDF...")
            rdf_data = generate_rdf(
                extraction_result,
                relationships or [],
            )

            # Call Layer 3 ingest API
            logger.info(f"Sending {len(rdf_data)} bytes to Layer 3...")
            response = await self._ingest_rdf(
                rdf_data=rdf_data,
                source_url=source_url,
                extraction_job_id=extraction_job_id,
            )

            return response

        except Exception as e:
            logger.error(f"Ingestion failed for {extraction_job_id}: {e}")
            return IngestionResponse(
                success=False,
                ingestion_id="",
                entities_loaded=0,
                relationships_loaded=0,
                message="Ingestion failed",
                error=str(e),
            )

    async def _ingest_rdf(
        self,
        rdf_data: str,
        source_url: str,
        extraction_job_id: str,
    ) -> IngestionResponse:
        """Send RDF data to Layer 3 ingest API.

        Args:
            rdf_data: RDF Turtle format data
            source_url: Source document URL
            extraction_job_id: Job ID for tracking

        Returns:
            IngestionResponse
        """
        payload = {
            "rdf_data": rdf_data,
            "format": "turtle",
            "source_id": source_url,
            "extraction_job_id": extraction_job_id,
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self._client.post(
                    "/v1/ingest",
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                data = response.json()
                return IngestionResponse(
                    success=True,
                    ingestion_id=data.get("ingestion_id", ""),
                    entities_loaded=data.get("entities_loaded", 0),
                    relationships_loaded=data.get("relationships_loaded", 0),
                    message=data.get("message", "Ingestion successful"),
                )

            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text}"
                if e.response.status_code in (429, 503, 504):  # Retryable
                    logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                    continue
                break  # Non-retryable
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2**attempt)

        return IngestionResponse(
            success=False,
            ingestion_id="",
            entities_loaded=0,
            relationships_loaded=0,
            message="All retry attempts failed",
            error=last_error,
        )

    async def get_ingestion_status(self, ingestion_id: str) -> IngestionStatus:
        """Check status of an ingestion job via canonical L3 endpoint.

        Calls GET /v1/ingest/status/{ingestion_id} (canonical route).
        L3 also provides backward-compatible alias /v1/ingest/{id}/status.

        Args:
            ingestion_id: Ingestion job ID (treated as source_id in L3)

        Returns:
            IngestionStatus with current state
        """
        try:
            response = await self._client.get(f"/v1/ingest/status/{ingestion_id}")
            response.raise_for_status()
            data = response.json()

            return IngestionStatus(
                ingestion_id=ingestion_id,
                status=data.get("status", "unknown"),
                progress_percent=data.get("progress_percent", 0.0),
                entities_processed=data.get("entities_processed", 0),
                entities_total=data.get("entities_total", 0),
                error_message=data.get("error_message"),
            )
        except Exception as e:
            logger.error(f"Failed to get ingestion status: {e}")
            return IngestionStatus(
                ingestion_id=ingestion_id,
                status="error",
                progress_percent=0.0,
                entities_processed=0,
                entities_total=0,
                error_message=str(e),
            )

    async def query_entities(
        self,
        entity_type: str | None = None,
        query: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Query entities from Layer 3 Knowledge Graph.

        Args:
            entity_type: Filter by entity type (Capability, UseCase, etc.)
            query: Full-text search query
            limit: Maximum results

        Returns:
            List of entity dictionaries
        """
        params = {"limit": limit}
        if entity_type:
            params["entity_type"] = entity_type
        if query:
            params["q"] = query

        try:
            response = await self._client.get("/v1/entities", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("entities", [])
        except Exception as e:
            logger.error(f"Entity query failed: {e}")
            return []

    async def graph_rag_query(
        self,
        question: str,
        max_hops: int = 3,
        entity_type: str | None = None,
    ) -> dict[str, Any]:
        """Execute GraphRAG query on Layer 3.

        Args:
            question: Natural language question
            max_hops: Maximum traversal depth
            entity_type: Optional entity type filter

        Returns:
            GraphRAG response with entities, relationships, context
        """
        payload = {
            "query": question,
            "max_hops": max_hops,
        }
        if entity_type:
            payload["entity_type"] = entity_type

        try:
            response = await self._client.post("/v1/query/graph", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"GraphRAG query failed: {e}")
            return Layer3KnowledgeClient_graph_rag_queryResult.model_validate({"error": str(e), "entities": [], "relationships": []})

    async def initialize_schema(self, drop_existing: bool = False) -> bool:
        """Initialize Neo4j schema (constraints, indexes).

        Args:
            drop_existing: If True, drops existing schema first

        Returns:
            True if successful
        """
        try:
            response = await self._client.post(
                "/v1/schema/initialize",
                json={"drop_existing": drop_existing},
            )
            response.raise_for_status()
            data = response.json()
            success = data.get("success", False)
            if success:
                logger.info("Schema initialized successfully")
            else:
                logger.error(f"Schema initialization failed: {data}")
            return success
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            return False


# Convenience functions for common use cases
async def ingest_to_knowledge_graph(
    extraction_result: ExtractionResult,
    source_url: str,
    extraction_job_id: str,
    base_url: str | None = None,
) -> IngestionResponse:
    """One-shot function to ingest extraction results.

    Args:
        extraction_result: Entities and relationships
        source_url: Source document URL
        extraction_job_id: Job ID for tracking
        base_url: Optional Layer 3 URL override

    Returns:
        IngestionResponse
    """
    client = Layer3KnowledgeClient(base_url=base_url)
    try:
        return await client.ingest_extraction_result(
            extraction_result=extraction_result,
            source_url=source_url,
            extraction_job_id=extraction_job_id,
        )
    finally:
        await client.close()
