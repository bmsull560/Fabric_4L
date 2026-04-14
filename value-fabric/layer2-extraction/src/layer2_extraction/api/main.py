"""FastAPI application for Layer 2: Extraction Pipeline.

Provides REST API endpoints for:
- Extracting entities from content
- Batch extraction jobs
- Ontology queries
- Extraction status and results
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

# Third-party imports for health check
try:
    import psutil
except ImportError:
    psutil = None  # Health check will work without system metrics

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

# Shared identity imports for authentication
# Layer2 requires shared.identity for all audit endpoints - fail fast if unavailable
try:
    from shared.identity.context import RequestContext
    from shared.identity.dependencies import require_authenticated
    _SHARED_IDENTITY_AVAILABLE = True
except ImportError:
    _SHARED_IDENTITY_AVAILABLE = False
    RequestContext = None  # type: ignore[assignment,misc]

    async def require_authenticated():  # type: ignore[misc]
        """Stub that raises when shared.identity is not installed."""
        raise RuntimeError(
            "shared.identity package is required for Layer2 authentication. "
            "Install the shared package or set up the Python path correctly."
        )

from layer2_extraction.alignment import SemanticAligner
from layer2_extraction.api.websocket import PipelineStage, get_pipeline_ws_manager, websocket_router
from layer2_extraction.extraction.chunker import chunk_markdown
from layer2_extraction.extraction.deduplicator import deduplicate_entities
from layer2_extraction.extraction.llm_extractor import EntityExtractor, RelationshipExtractor
from layer2_extraction.integration.layer3_client import Layer3KnowledgeClient
from layer2_extraction.integration.pending_ingestion_store import (
    PendingIngestionRecord,
    PendingIngestionStore,
    SqlitePendingIngestionStore,
    build_pending_ingestion_store,
)
from layer2_extraction.metrics import MetricsMiddleware, get_metrics, initialize_metrics
from layer2_extraction.models import (
    ExtractionResult,
    Relationship,
)
from layer2_extraction.output.provenance import (
    ExtractionStep,
    get_provenance_tracker,
)
from layer2_extraction.output.rdf_generator import generate_rdf
from layer2_extraction.validation import EntailmentValidator, ValidationSeverity

logger = logging.getLogger(__name__)

# App start time for uptime calculation
_app_start_time = time.time()

# WebSocket manager for real-time pipeline streaming
_ws_manager = get_pipeline_ws_manager()

# Initialize Prometheus metrics
metrics = initialize_metrics()

# Initialize FastAPI app
app = FastAPI(
    title="Value Fabric - Extraction Pipeline",
    description="Ontology-guided extraction of entities from unstructured text to RDF/OWL",
    version="1.0.0",
)

# Add metrics middleware if available
if metrics:
    metrics_middleware = MetricsMiddleware(metrics)
    app.middleware("http")(metrics_middleware)

# GovernanceMiddleware — verifies JWTs and resolves tenant/user context.
try:
    from shared.identity.middleware import GovernanceMiddleware

    app.add_middleware(GovernanceMiddleware, api_key_resolver=None)
except ImportError:
    import logging as _log

    _log.getLogger(__name__).warning(
        "shared.identity not importable — GovernanceMiddleware skipped in L2. "
        "Ensure the shared package is installed."
    )

# CORS middleware with production validation (P0-20)
# Note: allow_origins=["*"] cannot be used with allow_credentials=True per browser security spec
_environment = os.getenv("ENVIRONMENT", "development")
_cors_origins_env = os.getenv("CORS_ORIGINS", "")

if _environment == "production" and not _cors_origins_env:
    raise RuntimeError(
        "FATAL: CORS_ORIGINS environment variable must be set in production. "
        "Use 'https://yourdomain.com' or comma-separated list of allowed origins."
    )

# Parse CORS origins, filtering out empty strings from trailing commas
allow_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()] if _cors_origins_env else ["*"]
# Credentials can only be allowed with specific origins, never with wildcard (browser security requirement)
allow_credentials = "*" not in allow_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include WebSocket router for real-time pipeline streaming
app.include_router(websocket_router, prefix="/v1")

# Lazy initialization of extractors to avoid import-time side effects
_entity_extractor = None
_relationship_extractor = None


def get_entity_extractor():
    """Get or create the entity extractor (lazy initialization)."""
    global _entity_extractor
    if _entity_extractor is None:
        _entity_extractor = EntityExtractor(
            api_key=os.getenv("OPENAI_API_KEY"), model=os.getenv("LLM_MODEL", "gpt-4o")
        )
    return _entity_extractor


def get_relationship_extractor():
    """Get or create the relationship extractor (lazy initialization)."""
    global _relationship_extractor
    if _relationship_extractor is None:
        _relationship_extractor = RelationshipExtractor(
            api_key=os.getenv("OPENAI_API_KEY"), model=os.getenv("LLM_MODEL", "gpt-4o")
        )
    return _relationship_extractor


# Request/Response Models
class ExtractRequest(BaseModel):
    """Request body for extraction endpoint."""

    content_id: str = Field(..., description="ID of content to extract from (from Layer 1)")
    source_url: str = Field(..., description="URL of source document")
    markdown_content: str = Field(..., description="Markdown content to extract from")
    extraction_config: dict = Field(
        default_factory=lambda: {
            "entity_types": ["Capability", "UseCase", "Persona", "ValueDriver"],
            "confidence_threshold": 0.75,
            "chunk_size": 2000,
            "chunk_overlap": 200,
        }
    )


class ExtractResponse(BaseModel):
    """Response from extraction endpoint."""

    extraction_job_id: str
    status: str
    message: str


class ExtractionStatusResponse(BaseModel):
    """Status of a combined extraction + ingestion pipeline job."""

    job_id: str
    overall_status: str
    extraction_status: str
    ingestion_status: str
    entities_extracted: int
    relationships_extracted: int
    retry_count: int = 0
    last_error: str | None = None
    next_retry_at: datetime | None = None
    started_at: datetime
    completed_at: datetime | None


class EntityListResponse(BaseModel):
    """List of entities in the ontology."""

    entity_type: str
    entities: list[dict]
    total: int


class RelationshipsResponse(BaseModel):
    """Relationships for an entity."""

    entity_id: str
    incoming: list[dict]
    outgoing: list[dict]


class ProvenanceResponse(BaseModel):
    """Provenance chain for an entity or output."""

    activity_id: str
    source: dict
    extraction: dict
    steps: list[dict]
    output: dict


class ExtractAndIngestResponse(BaseModel):
    """Response for combined extract-and-ingest endpoint."""

    job_id: str
    overall_status: str
    extraction_status: str
    ingestion_status: str
    message: str


@dataclass
class PipelineJob:
    """In-memory pipeline job state for external status contract."""

    job_id: str
    extraction_status: str
    ingestion_status: str
    overall_status: str
    entities_extracted: int
    relationships_extracted: int
    retry_count: int
    last_error: str | None
    next_retry_at: datetime | None
    started_at: datetime
    completed_at: datetime | None


@dataclass
class ExtractionArtifacts:
    """Outputs from extraction pipeline used by ingestion step."""

    result: ExtractionResult
    relationships: list[Relationship]


PIPELINE_JOBS: dict[str, PipelineJob] = {}
RETRY_POLL_SECONDS = int(os.getenv("INGESTION_RETRY_POLL_SECONDS", "30"))
RETRY_BASE_SECONDS = int(os.getenv("INGESTION_RETRY_BASE_SECONDS", "60"))
MAX_INGESTION_RETRIES = int(os.getenv("INGESTION_MAX_RETRIES", "5"))
_retry_task: asyncio.Task | None = None
_UNSET = object()

try:
    pending_ingestion_store: PendingIngestionStore = build_pending_ingestion_store()
except Exception as exc:
    logger.warning(
        "Failed to initialize configured pending-ingestion store, falling back to SQLite: %s",
        exc,
    )
    pending_ingestion_store = SqlitePendingIngestionStore(
        os.getenv("PENDING_INGESTION_SQLITE_PATH", "./data/pending_ingestion.db")
    )


def _compute_overall_status(extraction_status: str, ingestion_status: str) -> str:
    if extraction_status == "failed" or ingestion_status == "failed":
        return "failed"
    if extraction_status in {"pending", "running"}:
        return "running"
    if extraction_status == "completed" and ingestion_status in {"pending", "queued"}:
        return "partial"
    if extraction_status == "completed" and ingestion_status == "running":
        return "running"
    if extraction_status == "completed" and ingestion_status in {"completed", "skipped"}:
        return "completed"
    return "pending"


def _set_pipeline_job(
    job_id: str,
    extraction_status: str | None = None,
    ingestion_status: str | None = None,
    entities_extracted: int | None = None,
    relationships_extracted: int | None = None,
    retry_count: int | None = None,
    last_error: object = _UNSET,
    next_retry_at: object = _UNSET,
    completed_at: datetime | None = None,
) -> None:
    job = PIPELINE_JOBS[job_id]
    if extraction_status is not None:
        job.extraction_status = extraction_status
    if ingestion_status is not None:
        job.ingestion_status = ingestion_status
    if entities_extracted is not None:
        job.entities_extracted = entities_extracted
    if relationships_extracted is not None:
        job.relationships_extracted = relationships_extracted
    if retry_count is not None:
        job.retry_count = retry_count
    if last_error is not _UNSET:
        job.last_error = last_error
    if next_retry_at is not _UNSET:
        job.next_retry_at = next_retry_at
    if completed_at is not None:
        job.completed_at = completed_at
    job.overall_status = _compute_overall_status(job.extraction_status, job.ingestion_status)


def _pipeline_response(job: PipelineJob) -> ExtractionStatusResponse:
    return ExtractionStatusResponse(
        job_id=job.job_id,
        overall_status=job.overall_status,
        extraction_status=job.extraction_status,
        ingestion_status=job.ingestion_status,
        entities_extracted=job.entities_extracted,
        relationships_extracted=job.relationships_extracted,
        retry_count=job.retry_count,
        last_error=job.last_error,
        next_retry_at=job.next_retry_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


def _serialize_artifacts(artifacts: ExtractionArtifacts) -> tuple[str, str]:
    result_json = json.dumps(artifacts.result.model_dump(mode="json"))
    relationships_json = json.dumps([r.model_dump(mode="json") for r in artifacts.relationships])
    return result_json, relationships_json


def _deserialize_artifacts(result_json: str, relationships_json: str) -> ExtractionArtifacts:
    result = ExtractionResult(**json.loads(result_json))
    relationships = [Relationship(**item) for item in json.loads(relationships_json)]
    return ExtractionArtifacts(result=result, relationships=relationships)


async def _queue_for_retry(
    job_id: str,
    source_url: str,
    artifacts: ExtractionArtifacts,
    last_error: str,
    retry_count: int,
) -> None:
    delay_seconds = RETRY_BASE_SECONDS * max(1, 2 ** max(retry_count - 1, 0))
    next_retry_at = datetime.utcnow().timestamp() + delay_seconds
    next_retry_dt = datetime.utcfromtimestamp(next_retry_at)
    result_json, relationships_json = _serialize_artifacts(artifacts)

    await pending_ingestion_store.enqueue(
        job_id=job_id,
        source_url=source_url,
        extraction_result_json=result_json,
        relationships_json=relationships_json,
        retry_count=retry_count,
        next_retry_at=next_retry_dt,
        max_retries=MAX_INGESTION_RETRIES,
        last_error=last_error,
    )

    _set_pipeline_job(
        job_id,
        ingestion_status="queued",
        retry_count=retry_count,
        last_error=last_error,
        next_retry_at=next_retry_dt,
    )


async def _attempt_ingestion(job_id: str, source_url: str, artifacts: ExtractionArtifacts) -> bool:
    client = Layer3KnowledgeClient()
    try:
        _set_pipeline_job(job_id, ingestion_status="running", next_retry_at=None)

        # Broadcast ingestion start
        await _ws_manager.broadcast_ingestion_status(
            job_id=job_id,
            status="running",
            retry_count=PIPELINE_JOBS[job_id].retry_count,
            max_retries=MAX_INGESTION_RETRIES,
        )

        response = await client.ingest_extraction_result(
            extraction_result=artifacts.result,
            source_url=source_url,
            extraction_job_id=job_id,
            relationships=artifacts.relationships,
        )
        if response.success:
            _set_pipeline_job(
                job_id,
                ingestion_status="completed",
                last_error=None,
                next_retry_at=None,
                completed_at=datetime.utcnow(),
            )

            # Broadcast ingestion success
            await _ws_manager.broadcast_ingestion_status(
                job_id=job_id,
                status="completed",
                retry_count=PIPELINE_JOBS[job_id].retry_count,
                max_retries=MAX_INGESTION_RETRIES,
                entities_loaded=response.entities_loaded,
                relationships_loaded=response.relationships_loaded,
            )

            # Broadcast overall pipeline completion
            job = PIPELINE_JOBS[job_id]
            await _ws_manager.broadcast_pipeline_complete(
                job_id=job_id,
                status="completed",
                entities_extracted=job.entities_extracted,
                relationships_extracted=job.relationships_extracted,
                entities_loaded=response.entities_loaded,
                relationships_loaded=response.relationships_loaded,
            )

            await pending_ingestion_store.complete(job_id)
            return True

        retry_count = PIPELINE_JOBS[job_id].retry_count + 1

        # Broadcast ingestion failure with retry
        await _ws_manager.broadcast_ingestion_status(
            job_id=job_id,
            status="retrying" if retry_count <= MAX_INGESTION_RETRIES else "failed",
            retry_count=retry_count,
            max_retries=MAX_INGESTION_RETRIES,
            error=response.error or response.message,
        )

        await _queue_for_retry(
            job_id=job_id,
            source_url=source_url,
            artifacts=artifacts,
            last_error=response.error or response.message,
            retry_count=retry_count,
        )
        return False
    finally:
        await client.close()


async def _process_pending_ingestions() -> None:
    now = datetime.utcnow()
    records: list[PendingIngestionRecord] = await pending_ingestion_store.get_due(now)
    for record in records:
        if record.job_id not in PIPELINE_JOBS:
            PIPELINE_JOBS[record.job_id] = PipelineJob(
                job_id=record.job_id,
                extraction_status="completed",
                ingestion_status="queued",
                overall_status="partial",
                entities_extracted=0,
                relationships_extracted=0,
                retry_count=record.retry_count,
                last_error=record.last_error,
                next_retry_at=record.next_retry_at,
                started_at=datetime.utcnow(),
                completed_at=None,
            )

        artifacts = _deserialize_artifacts(record.extraction_result_json, record.relationships_json)
        client = Layer3KnowledgeClient()
        try:
            healthy = await client.health_check()
        finally:
            await client.close()

        if not healthy:
            retry_count = record.retry_count + 1
            if retry_count >= record.max_retries:
                await pending_ingestion_store.complete(record.job_id)
                _set_pipeline_job(
                    record.job_id,
                    ingestion_status="failed",
                    retry_count=retry_count,
                    last_error="Layer 3 unavailable after max retries",
                    next_retry_at=None,
                    completed_at=datetime.utcnow(),
                )
            else:
                delay_seconds = RETRY_BASE_SECONDS * (2 ** max(record.retry_count, 0))
                next_retry_at = datetime.utcfromtimestamp(
                    datetime.utcnow().timestamp() + delay_seconds
                )
                await pending_ingestion_store.reschedule(
                    job_id=record.job_id,
                    retry_count=retry_count,
                    last_error="Layer 3 unavailable",
                    next_retry_at=next_retry_at,
                )
                _set_pipeline_job(
                    record.job_id,
                    ingestion_status="queued",
                    retry_count=retry_count,
                    last_error="Layer 3 unavailable",
                    next_retry_at=next_retry_at,
                )
            continue

        success = await _attempt_ingestion(record.job_id, record.source_url, artifacts)
        if not success:
            metadata = await pending_ingestion_store.get_retry_metadata(record.job_id)
            if metadata:
                _set_pipeline_job(
                    record.job_id,
                    retry_count=metadata.get(
                        "retry_count", PIPELINE_JOBS[record.job_id].retry_count
                    ),
                    last_error=metadata.get("last_error"),
                    next_retry_at=(
                        datetime.fromisoformat(metadata["next_retry_at"])
                        if metadata.get("next_retry_at")
                        else None
                    ),
                )


async def _pending_ingestion_retry_loop() -> None:
    while True:
        try:
            await _process_pending_ingestions()
        except Exception as exc:
            logger.exception("Pending ingestion retry loop error: %s", exc)
        await asyncio.sleep(RETRY_POLL_SECONDS)


@app.on_event("startup")
async def startup_event() -> None:
    global _retry_task
    if _retry_task is None:
        _retry_task = asyncio.create_task(_pending_ingestion_retry_loop())

    # Start WebSocket manager for real-time streaming
    await _ws_manager.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    global _retry_task
    if _retry_task:
        _retry_task.cancel()
        try:
            await _retry_task
        except asyncio.CancelledError:
            pass
        _retry_task = None

    # Stop WebSocket manager
    await _ws_manager.stop()


# Background task for extraction
async def run_extraction(
    job_id: str,
    source_url: str,
    content: str,
    config: dict,
    mark_pipeline_complete: bool = True,
):
    """Background extraction task.

    Executes the full 6-stage extraction pipeline:
    1. Chunk input
    2. Extract entities
    3. Extract relationships
    4. Deduplicate
    5. Validate
    6. Generate RDF
    """
    tracker = get_provenance_tracker()

    # Calculate content hash for provenance
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    # Start provenance tracking
    activity = tracker.start_activity(
        activity_id=job_id, source_url=source_url, content_hash=content_hash
    )

    if job_id not in PIPELINE_JOBS:
        PIPELINE_JOBS[job_id] = PipelineJob(
            job_id=job_id,
            extraction_status="pending",
            ingestion_status="skipped",
            overall_status="pending",
            entities_extracted=0,
            relationships_extracted=0,
            retry_count=0,
            last_error=None,
            next_retry_at=None,
            started_at=datetime.utcnow(),
            completed_at=None,
        )

    _set_pipeline_job(job_id, extraction_status="running")

    # Broadcast pipeline start
    await _ws_manager.broadcast_stage_start(
        job_id=job_id, stage=PipelineStage.CHUNKING, stage_number=1, total_stages=6
    )

    try:
        # Stage 1: Chunking
        step1 = ExtractionStep(step_name="chunking", started_at=datetime.utcnow())

        chunk_size = config.get("chunk_size", 2000)
        chunk_overlap = config.get("chunk_overlap", 200)

        chunks = chunk_markdown(
            content, source_url=source_url, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

        step1.completed_at = datetime.utcnow()
        activity.add_step(step1)

        # Broadcast chunking complete
        await _ws_manager.broadcast_stage_complete(
            job_id=job_id,
            stage=PipelineStage.CHUNKING,
            stage_number=1,
            total_stages=6,
            result_summary={"chunks_created": len(chunks)},
        )

        # Stage 2 & 3: Entity and Relationship Extraction
        await _ws_manager.broadcast_stage_start(
            job_id=job_id,
            stage=PipelineStage.ENTITY_EXTRACTION,
            stage_number=2,
            total_stages=6,
            metadata={"total_chunks": len(chunks)},
        )

        step2 = ExtractionStep(step_name="entity_extraction", started_at=datetime.utcnow())

        all_entities = {
            "capabilities": [],
            "use_cases": [],
            "personas": [],
            "value_drivers": [],
            "features": [],
        }
        all_relationships = []

        confidence_threshold = config.get("confidence_threshold", 0.75)

        for i, chunk in enumerate(chunks):
            # Broadcast progress every chunk
            if i % max(1, len(chunks) // 10) == 0 or i == len(chunks) - 1:
                await _ws_manager.broadcast_stage_progress(
                    job_id=job_id,
                    stage=PipelineStage.ENTITY_EXTRACTION,
                    stage_number=2,
                    total_stages=6,
                    items_processed=i + 1,
                    items_total=len(chunks),
                    stage_percent=int((i + 1) / len(chunks) * 100),
                )

            # Extract entities from chunk
            entities = await get_entity_extractor().extract_entities(
                text=chunk.content,
                source_url=source_url,
                extraction_job_id=job_id,
                confidence_threshold=confidence_threshold,
            )

            # Collect entities
            for entity_type, entity_list in entities.items():
                all_entities[entity_type].extend(entity_list)

            # Extract relationships
            relationships = await get_relationship_extractor().extract_relationships(
                text=chunk.content,
                entities=entities,
                source_url=source_url,
                extraction_job_id=job_id,
                confidence_threshold=confidence_threshold
                - 0.05,  # Slightly lower for relationships
            )
            all_relationships.extend(relationships)

        step2.completed_at = datetime.utcnow()
        total_entities = sum(len(v) for v in all_entities.values())
        step2.entities_extracted = total_entities
        activity.add_step(step2)

        # Broadcast entity extraction complete
        await _ws_manager.broadcast_stage_complete(
            job_id=job_id,
            stage=PipelineStage.ENTITY_EXTRACTION,
            stage_number=2,
            total_stages=6,
            result_summary={
                "entities_extracted": total_entities,
                "relationships_found": len(all_relationships),
                "chunks_processed": len(chunks),
            },
        )

        # Stage 3: Semantic Alignment
        await _ws_manager.broadcast_stage_start(
            job_id=job_id,
            stage=PipelineStage.SEMANTIC_ALIGNMENT,
            stage_number=3,
            total_stages=6,
            metadata={"entity_types": list(all_entities.keys())},
        )
        step_align = ExtractionStep(step_name="semantic_alignment", started_at=datetime.utcnow())

        aligner = SemanticAligner(similarity_threshold=0.85, api_key=os.getenv("OPENAI_API_KEY"))

        # Align each entity type
        aligned_entities = {}
        for entity_type, entity_list in all_entities.items():
            if entity_list:
                aligned_list, _ = await aligner.align_entities(entity_list)
                aligned_entities[entity_type] = aligned_list
            else:
                aligned_entities[entity_type] = []

        all_entities = aligned_entities

        step_align.completed_at = datetime.utcnow()
        activity.add_step(step_align)

        # Broadcast alignment complete
        await _ws_manager.broadcast_stage_complete(
            job_id=job_id, stage=PipelineStage.SEMANTIC_ALIGNMENT, stage_number=3, total_stages=6
        )

        # Stage 4: Deduplication
        await _ws_manager.broadcast_stage_start(
            job_id=job_id,
            stage=PipelineStage.DEDUPLICATION,
            stage_number=4,
            total_stages=6,
            metadata={"entities_before": total_entities},
        )
        step3 = ExtractionStep(step_name="deduplication", started_at=datetime.utcnow())

        deduplicated = await deduplicate_entities(
            all_entities,
            api_key=os.getenv("OPENAI_API_KEY"),
            similarity_threshold=0.85,
            relationships=all_relationships,
            enable_coreference=True,
        )

        step3.completed_at = datetime.utcnow()
        activity.add_step(step3)

        entities_after = sum(len(v) for v in deduplicated.values())

        # Broadcast deduplication complete
        await _ws_manager.broadcast_stage_complete(
            job_id=job_id,
            stage=PipelineStage.DEDUPLICATION,
            stage_number=4,
            total_stages=6,
            result_summary={
                "entities_before": total_entities,
                "entities_after": entities_after,
                "duplicates_removed": total_entities - entities_after,
            },
        )

        # Stage 5: Validation (EntailmentValidator with 6 validation rules)
        await _ws_manager.broadcast_stage_start(
            job_id=job_id, stage=PipelineStage.VALIDATION, stage_number=5, total_stages=6
        )
        step4 = ExtractionStep(step_name="validation", started_at=datetime.utcnow())

        # Create extraction result
        result = ExtractionResult(
            job_id=job_id,
            source_url=source_url,
            capabilities=deduplicated.get("capabilities", []),
            use_cases=deduplicated.get("use_cases", []),
            personas=deduplicated.get("personas", []),
            value_drivers=deduplicated.get("value_drivers", []),
            features=deduplicated.get("features", []),
            chunks_processed=len(chunks),
        )

        # Run entailment validation
        validator = EntailmentValidator()
        validation_results = validator.validate(result, all_relationships)

        # Check for validation errors
        errors = [
            r for r in validation_results if r.severity == ValidationSeverity.ERROR and not r.passed
        ]
        warnings = [
            r
            for r in validation_results
            if r.severity == ValidationSeverity.WARNING and not r.passed
        ]

        if errors:
            # Add errors to result
            result.errors.extend([f"[ERROR] {e.rule_id}: {e.message}" for e in errors])
        if warnings:
            # Log warnings but continue
            result.errors.extend([f"[WARNING] {w.rule_id}: {w.message}" for w in warnings])

        step4.completed_at = datetime.utcnow()
        step4.entities_extracted = len(validation_results)  # Track validation results count
        activity.add_step(step4)

        # Broadcast validation complete
        await _ws_manager.broadcast_stage_complete(
            job_id=job_id,
            stage=PipelineStage.VALIDATION,
            stage_number=5,
            total_stages=6,
            result_summary={
                "passed": len([r for r in validation_results if r.passed]),
                "failed": len([r for r in validation_results if not r.passed]),
                "errors": len(errors),
                "warnings": len(warnings),
            },
        )

        # Stage 6: RDF Generation
        await _ws_manager.broadcast_stage_start(
            job_id=job_id, stage=PipelineStage.RDF_GENERATION, stage_number=6, total_stages=6
        )
        step5 = ExtractionStep(step_name="rdf_generation", started_at=datetime.utcnow())

        rdf_content = generate_rdf(result, all_relationships)

        # Broadcast RDF generation complete
        await _ws_manager.broadcast_stage_complete(
            job_id=job_id,
            stage=PipelineStage.RDF_GENERATION,
            stage_number=6,
            total_stages=6,
            result_summary={
                "rdf_size_bytes": len(rdf_content.encode("utf-8")),
                "entities_in_rdf": entities_after,
                "relationships_in_rdf": len(all_relationships),
            },
        )

        # Save RDF to file (in production, this would go to S3/MinIO)
        output_dir = os.getenv("RDF_OUTPUT_DIR", "/tmp/rdf")
        os.makedirs(output_dir, exist_ok=True)
        rdf_path = f"{output_dir}/{job_id}.ttl"

        with open(rdf_path, "w") as f:
            f.write(rdf_content)

        step5.completed_at = datetime.utcnow()
        activity.add_step(step5)

        # Complete activity
        activity.output_entities = [e.id for e in result.get_all_entities()]
        activity.output_relationships = [r.id for r in all_relationships]
        activity.complete(rdf_path=rdf_path)

        _set_pipeline_job(
            job_id,
            extraction_status="completed",
            entities_extracted=len(activity.output_entities),
            relationships_extracted=len(activity.output_relationships),
            completed_at=datetime.utcnow() if mark_pipeline_complete else None,
        )

        # Broadcast extraction-only completion (if not going to ingestion)
        if mark_pipeline_complete:
            await _ws_manager.broadcast_pipeline_complete(
                job_id=job_id,
                status="completed",
                entities_extracted=len(activity.output_entities),
                relationships_extracted=len(activity.output_relationships),
                rdf_path=rdf_path,
            )

        return ExtractionArtifacts(result=result, relationships=all_relationships)

    except Exception as e:
        error_msg = str(e)
        activity.fail(error_msg)
        _set_pipeline_job(
            job_id,
            extraction_status="failed",
            last_error=error_msg,
            completed_at=datetime.utcnow(),
        )

        # Broadcast extraction failure
        await _ws_manager.broadcast_error(
            job_id=job_id,
            stage=PipelineStage.RDF_GENERATION,  # Default to last stage
            error=error_msg,
            recoverable=False,
        )

        # Broadcast pipeline completion as failed
        await _ws_manager.broadcast_pipeline_complete(
            job_id=job_id,
            status="failed",
            entities_extracted=0,
            relationships_extracted=0,
            errors=[error_msg],
        )

        raise


async def run_extract_and_ingest(
    job_id: str,
    source_url: str,
    content: str,
    config: dict,
) -> None:
    """Run extraction and ingestion in one background pipeline."""
    try:
        artifacts = await run_extraction(
            job_id,
            source_url,
            content,
            config,
            mark_pipeline_complete=False,
        )
    except Exception:
        return

    if not artifacts:
        return

    client = Layer3KnowledgeClient()
    try:
        healthy = await client.health_check()
    finally:
        await client.close()

    if not healthy:
        retry_count = PIPELINE_JOBS[job_id].retry_count + 1

        # Broadcast ingestion queued for retry
        await _ws_manager.broadcast_ingestion_status(
            job_id=job_id,
            status="queued",
            retry_count=retry_count,
            max_retries=MAX_INGESTION_RETRIES,
            error="Layer 3 unavailable - queued for retry",
        )

        await _queue_for_retry(
            job_id=job_id,
            source_url=source_url,
            artifacts=artifacts,
            last_error="Layer 3 unavailable",
            retry_count=retry_count,
        )
        return

    await _attempt_ingestion(job_id, source_url, artifacts)


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint with real metrics and dependency status."""
    start_time = time.time()
    uptime = time.time() - _app_start_time

    metrics = get_metrics()
    total_requests = 0
    active_connections = 0

    if metrics and metrics.config.enabled:
        try:
            requests_counter = metrics._metrics.get("requests_total", {})
            total_requests = (
                sum(
                    v._value.get() if hasattr(v._value, "get") else v._value
                    for method_dict in requests_counter._metrics.values()
                    for endpoint_dict in method_dict.values()
                    for v in endpoint_dict.values()
                )
                if hasattr(requests_counter, "_metrics")
                else 0
            )
        except (AttributeError, TypeError):
            total_requests = 0

        try:
            active_connections = int(
                metrics._metrics.get("active_connections", {}).get("total", {}).get("_value", 0)
            )
        except (AttributeError, TypeError):
            active_connections = 0

    # Check Layer 3 dependency
    dependencies = []
    overall_status = "healthy"

    try:
        from layer2_extraction.integration.layer3_client import Layer3KnowledgeClient

        l3_start = time.time()
        l3_client = Layer3KnowledgeClient()
        l3_healthy = await l3_client.health_check()
        l3_response_ms = round((time.time() - l3_start) * 1000, 2)
        await l3_client.close()

        dependencies.append(
            {
                "name": "layer3_knowledge",
                "status": "healthy" if l3_healthy else "unhealthy",
                "response_time_ms": l3_response_ms,
                "error": None if l3_healthy else "Layer 3 returned unhealthy status",
            }
        )

        if not l3_healthy:
            overall_status = "degraded"
    except Exception as e:
        dependencies.append(
            {
                "name": "layer3_knowledge",
                "status": "unhealthy",
                "response_time_ms": None,
                "error": str(e),
            }
        )
        overall_status = "degraded"

    total_response_ms = round((time.time() - start_time) * 1000, 2)

    # Update health metrics if available
    if metrics:
        metrics.set_health_status(overall_status == "healthy", component="api")
        l3_dep_healthy = any(
            d["name"] == "layer3_knowledge" and d["status"] == "healthy" for d in dependencies
        )
        metrics.set_health_status(l3_dep_healthy, component="layer3")

    # Build system metrics if psutil is available
    system_metrics = {"active_connections": active_connections, "total_requests": total_requests}
    if psutil:
        memory_info = psutil.virtual_memory()
        system_metrics["memory_usage_mb"] = memory_info.used / (1024 * 1024)
        system_metrics["cpu_percent"] = psutil.cpu_percent()

    return {
        "status": overall_status,
        "service": "layer2-extraction",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime,
        "response_time_ms": total_response_ms,
        "dependencies": dependencies,
        "metrics": system_metrics,
    }


@app.get("/metrics")
async def metrics_endpoint(request: Request):
    """Prometheus metrics endpoint."""
    metrics = get_metrics()

    if not metrics:
        return Response(
            content="Metrics collection is disabled", status_code=503, media_type="text/plain"
        )

    try:
        metrics_data = metrics.get_metrics()
        return Response(content=metrics_data, media_type="text/plain; version=0.0.4; charset=utf-8")
    except Exception as e:
        return Response(
            content=f"Error generating metrics: {e}", status_code=500, media_type="text/plain"
        )


@app.post("/v1/extract", response_model=ExtractResponse)
async def extract(request: ExtractRequest, background_tasks: BackgroundTasks):
    """Start an extraction job.

    Extracts entities and relationships from provided Markdown content
    and generates RDF/OWL output.
    """
    job_id = str(uuid4())

    PIPELINE_JOBS[job_id] = PipelineJob(
        job_id=job_id,
        extraction_status="pending",
        ingestion_status="skipped",
        overall_status="pending",
        entities_extracted=0,
        relationships_extracted=0,
        retry_count=0,
        last_error=None,
        next_retry_at=None,
        started_at=datetime.utcnow(),
        completed_at=None,
    )

    # Queue extraction as background task
    background_tasks.add_task(
        run_extraction,
        job_id=job_id,
        source_url=request.source_url,
        content=request.markdown_content,
        config=request.extraction_config,
    )

    return ExtractResponse(
        extraction_job_id=job_id, status="queued", message="Extraction job started"
    )


@app.post("/v1/extract-and-ingest", response_model=ExtractAndIngestResponse)
async def extract_and_ingest(
    request: ExtractRequest,
    background_tasks: BackgroundTasks,
):
    """Start a combined extraction and ingestion pipeline job."""
    job_id = str(uuid4())

    PIPELINE_JOBS[job_id] = PipelineJob(
        job_id=job_id,
        extraction_status="pending",
        ingestion_status="pending",
        overall_status="pending",
        entities_extracted=0,
        relationships_extracted=0,
        retry_count=0,
        last_error=None,
        next_retry_at=None,
        started_at=datetime.utcnow(),
        completed_at=None,
    )

    background_tasks.add_task(
        run_extract_and_ingest,
        job_id=job_id,
        source_url=request.source_url,
        content=request.markdown_content,
        config=request.extraction_config,
    )

    return ExtractAndIngestResponse(
        job_id=job_id,
        overall_status="pending",
        extraction_status="pending",
        ingestion_status="pending",
        message="Extraction and ingestion job started",
    )


@app.get("/v1/extract/status/{job_id}", response_model=ExtractionStatusResponse)
async def get_extraction_status(job_id: str):
    """Get status of a combined extraction and ingestion job."""
    job = PIPELINE_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return _pipeline_response(job)


@app.post("/v1/extract/batch")
async def extract_batch(requests: list[ExtractRequest], background_tasks: BackgroundTasks):
    """Start a batch extraction job."""
    batch_id = str(uuid4())
    job_ids = []

    for req in requests:
        job_id = str(uuid4())
        job_ids.append(job_id)
        background_tasks.add_task(
            run_extraction,
            job_id=job_id,
            source_url=req.source_url,
            content=req.markdown_content,
            config=req.extraction_config,
        )

    return {
        "batch_job_id": batch_id,
        "job_ids": job_ids,
        "status": "queued",
        "total_jobs": len(requests),
    }


@app.get("/v1/ontology/entities")
async def list_entities(
    entity_type: str | None = Query(
        None, enum=["Capability", "UseCase", "Persona", "ValueDriver", "Feature"]
    ),
    limit: int = Query(100, ge=1, le=1000),
):
    """List entities in the ontology.

    Note: In a full implementation, this would query a persistent store.
    For now, returns empty list (entities are in RDF files).
    """
    # This would query Neo4j or similar in production
    return EntityListResponse(entity_type=entity_type or "all", entities=[], total=0)


@app.get("/v1/ontology/relationships/{entity_id}")
async def get_relationships(entity_id: str):
    """Get relationships for an entity.

    Note: In a full implementation, this would query the graph database.
    """
    return RelationshipsResponse(entity_id=entity_id, incoming=[], outgoing=[])


@app.get("/v1/audit/trace/{job_id}", response_model=ProvenanceResponse)
async def get_provenance(
    job_id: str,
    ctx: RequestContext = Depends(require_authenticated),
):
    """Get full provenance trace for an extraction job. Requires authentication."""
    tracker = get_provenance_tracker()
    activity = tracker.get_activity(job_id)

    if not activity:
        raise HTTPException(status_code=404, detail="Job not found")

    chain = activity.get_provenance_chain()

    return ProvenanceResponse(
        activity_id=chain["activity_id"],
        source=chain["source"],
        extraction=chain["extraction"],
        steps=chain["steps"],
        output=chain["output"],
    )


@app.get("/v1/audit/entity/{entity_id}")
async def get_entity_provenance(
    entity_id: str,
    ctx: RequestContext = Depends(require_authenticated),
):
    """Get provenance for a specific entity. Requires authentication."""
    tracker = get_provenance_tracker()
    chain = tracker.get_provenance_for_entity(entity_id)

    if not chain:
        raise HTTPException(status_code=404, detail="Entity provenance not found")

    return chain


async def _job_event_generator(job_id: str):
    """Generate SSE events for a pipeline job.

    Yields Server-Sent Events with progress updates, status changes,
    and entity discovery from the extraction pipeline.
    """
    import asyncio
    import json

    last_status = None
    last_progress = -1
    sent_entities: set[str] = set()

    while True:
        job = PIPELINE_JOBS.get(job_id)

        if not job:
            # Job not found - send error and close
            yield f"event: error\ndata: {json.dumps({'message': f'Job {job_id} not found'})}\n\n"
            break

        # Calculate progress based on status
        status_progress_map = {
            "pending": 0,
            "running": 25,
            "partial": 75,
            "completed": 100,
            "failed": 100,
        }
        progress = status_progress_map.get(job.overall_status, 0)

        # Send status event on change
        if job.overall_status != last_status:
            last_status = job.overall_status
            event_data = {
                "type": "status",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": job.overall_status,
            }
            yield f"data: {json.dumps(event_data)}\n\n"

        # Send progress event on significant change (>= 5%) or at boundaries
        if abs(progress - last_progress) >= 5 or progress in [0, 50, 100]:
            last_progress = progress
            event_data = {
                "type": "progress",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": progress,
            }
            yield f"data: {json.dumps(event_data)}\n\n"

        # Send entity events for newly discovered entities
        # Note: In a real implementation, this would come from the job's entity cache
        # For now, we simulate based on extraction progress
        if job.entities_extracted > 0 and job.extraction_status == "running":
            entity_key = f"entity_{job_id}_{job.entities_extracted}"
            if entity_key not in sent_entities:
                sent_entities.add(entity_key)
                event_data = {
                    "type": "entity",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "data": {
                        "type": "Capability",
                        "name": f"Discovered Capability {job.entities_extracted}",
                    },
                }
                yield f"data: {json.dumps(event_data)}\n\n"

        # Send log events for status transitions
        if job.overall_status in ["running", "completed", "failed"]:
            log_levels = {"running": "info", "completed": "success", "failed": "error"}
            log_messages = {
                "running": f"Extraction pipeline {job_id} is running",
                "completed": f"Extraction pipeline {job_id} completed successfully",
                "failed": f"Extraction pipeline {job_id} failed: {job.last_error or 'Unknown error'}",
            }
            event_data = {
                "type": "log",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "level": log_levels.get(job.overall_status, "info"),
                    "message": log_messages.get(job.overall_status, f"Status: {job.overall_status}"),
                },
            }
            yield f"data: {json.dumps(event_data)}\n\n"

        # Check for completion
        if job.overall_status in ["completed", "failed"]:
            event_type = "complete" if job.overall_status == "completed" else "error"
            event_data = {
                "type": event_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": {
                    "job_id": job_id,
                    "status": job.overall_status,
                    "entities_extracted": job.entities_extracted,
                    "relationships_extracted": job.relationships_extracted,
                    "error": job.last_error if job.overall_status == "failed" else None,
                },
            }
            yield f"data: {json.dumps(event_data)}\n\n"
            break

        # Poll interval - check every 500ms for updates
        await asyncio.sleep(0.5)


@app.get("/extract/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    """Stream real-time events for a pipeline job via SSE.

    Returns a Server-Sent Events stream with progress updates,
    status changes, entity discovery, and log messages.

    Event types:
    - `progress`: Extraction progress percentage (0-100)
    - `status`: Job status changes (pending, running, completed, failed)
    - `log`: Pipeline log messages with timestamp and level
    - `entity`: Newly discovered entities during extraction
    - `complete`: Job completion event
    - `error`: Error event with details

    Args:
        job_id: The pipeline job ID to stream events for

    Returns:
        StreamingResponse with text/event-stream content type
    """
    if job_id not in PIPELINE_JOBS:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return StreamingResponse(
        _job_event_generator(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for SSE
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
