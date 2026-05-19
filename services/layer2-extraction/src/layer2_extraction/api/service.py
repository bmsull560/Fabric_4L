"""Layer 2 extraction API service layer."""

from __future__ import annotations

from pydantic import BaseModel

from layer2_extraction.extraction.chunker import SemanticChunker
from layer2_extraction.extraction.llm_extractor import EntityExtractor, RelationshipExtractor
from layer2_extraction.models.extraction_api import ExtractionResult


# ---------------------------------------------------------------------------
# API Schema stubs (route layer depends on these)
# ---------------------------------------------------------------------------


class ExtractionStatusResponse(BaseModel):
    job_id: str
    status: str = "unknown"
    progress: float = 0.0
    message: str | None = None


class ExtractRequest(BaseModel):
    content: str
    source_url: str = ""
    job_id: str = ""


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def get_extraction_status(job_id: str) -> ExtractionStatusResponse:
    """Get current extraction status for a job."""
    # TODO: integrate with real job store
    return ExtractionStatusResponse(job_id=job_id, status="pending", progress=0.0)


async def extract_batch(requests: list[ExtractRequest], background_tasks) -> dict:
    """Enqueue a batch of extraction jobs."""
    # TODO: integrate with real pipeline
    return {"batch_id": "stub", "queued": len(requests)}


async def stream_job_events(job_id: str):
    """Stream SSE events for a job."""
    # TODO: integrate with real event stream
    return {"job_id": job_id, "events": []}


async def handle_ingestion_completed(payload: dict) -> dict:
    """Handle notification from L1 that ingestion finished.

    Enqueues extraction for the ingested content.
    """
    from layer2_extraction.integration.job_store import build_job_store

    job_store = build_job_store()
    # Create a new extraction job linked to the L1 ingestion result
    job = await job_store.create(
        source_url=payload.get("output_url", ""),
        tenant_id=payload.get("tenant_id", "default"),
        metadata={
            "l1_job_id": payload.get("job_id"),
            "l1_target_id": payload.get("target_id"),
            "ingestion_status": payload.get("status"),
        },
    )
    return {
        "received": True,
        "l2_job_id": job.id if hasattr(job, "id") else str(job),
        "l1_job_id": payload.get("job_id"),
    }


async def health_check() -> dict:
    """Liveness probe."""
    return {"status": "ok", "service": "layer2-extraction"}


async def metrics_endpoint(request) -> dict:
    """Prometheus-style metrics stub."""
    return {"metrics": "stub"}


class ExtractionService:
    """Orchestrates the full extraction pipeline."""

    def __init__(self, api_key: str | None = None) -> None:
        self.chunker = SemanticChunker()
        self.entity_extractor = EntityExtractor(api_key=api_key)
        self.relationship_extractor = RelationshipExtractor(api_key=api_key)

    async def extract(
        self,
        content: str,
        source_url: str = "",
        job_id: str = "",
    ) -> ExtractionResult:
        """Run full extraction pipeline on content."""
        chunks = self.chunker.chunk_text(content, source_url=source_url)
        result = ExtractionResult(source_url=source_url)

        for chunk in chunks:
            entities = await self.entity_extractor.extract(
                chunk.content, source_url=source_url, job_id=job_id
            )
            result.capabilities.extend(entities.get("capabilities", []))
            result.use_cases.extend(entities.get("use_cases", []))
            result.personas.extend(entities.get("personas", []))
            result.value_drivers.extend(entities.get("value_drivers", []))

        all_entities = result.get_all_entities()
        relationships = await self.relationship_extractor.extract_relationships(
            content, all_entities, source_url=source_url, job_id=job_id
        )
        result.relationships = relationships
        return result
