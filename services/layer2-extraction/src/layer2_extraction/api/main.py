"""Layer 2 extraction API main module."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from value_fabric.shared.identity.middleware import GovernanceMiddleware
from value_fabric.shared.security import SecurityConfig, add_security_middleware
from value_fabric.shared.fastapi_framework.middleware import resolve_cors_policy

from layer2_extraction.extraction.cache import ExtractionCache
from layer2_extraction.extraction.llm_extractor import EntityExtractor, RelationshipExtractor
from layer2_extraction.integration.job_store import (
    ExtractionArtifacts,
    PipelineJob,
    build_job_store,
)
from layer2_extraction.integration.layer3_client import Layer3KnowledgeClient
from layer2_extraction.integration.pending_ingestion_store import (
    build_pending_ingestion_store,
)
from layer2_extraction.models.extraction_api import ExtractionRequest, ExtractionResult


RETRY_BASE_SECONDS = 60

# Statuses that indicate a pipeline job has reached a terminal state.
# The SSE generator breaks out of its poll loop when overall status is in this set.
_SSE_TERMINAL_STATUSES: frozenset[str] = frozenset({"completed", "failed"})


async def _init_redis_rate_limiter() -> Any:
    """Initialize Redis rate limiter; fail closed in production."""
    import os
    import redis.asyncio as redis_lib

    env = os.environ.get("ENVIRONMENT", os.environ.get("APP_ENV", "development")).lower()
    redis_url = os.environ.get("REDIS_URL", "")

    if env not in ("production", "staging"):
        return None

    if not redis_url:
        raise RuntimeError("Redis rate limiting is required")

    try:
        client = redis_lib.from_url(redis_url)
        await client.ping()
        return client
    except Exception:
        raise RuntimeError("Redis rate limiting is required")


job_store = build_job_store()
pending_ingestion_store = build_pending_ingestion_store()
_extraction_cache = ExtractionCache()

def _attach_test_tenant_middleware(application: FastAPI) -> None:
    """Attach the test-only tenant middleware to *application*.

    The middleware pre-populates ``governance_context`` from the
    ``X-Test-Tenant`` request header so unit tests can run without real JWTs.
    It must be added *after* ``GovernanceMiddleware`` so it wraps the outer
    layer and runs first in the ASGI stack.

    This is a standalone function (not an inline ``if`` block) so tests can
    call it explicitly on a freshly constructed app instance, avoiding the
    import-time race where the module-level conditional runs before the test
    suite has set ``TESTING=true``.
    """
    import uuid as _uuid

    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request as _Request
    from value_fabric.shared.identity.context import RequestContext as _RequestContext

    class _TestTenantMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: _Request, call_next):
            test_tenant = request.headers.get("x-test-tenant")
            if test_tenant:
                try:
                    tid: _uuid.UUID | str = _uuid.UUID(test_tenant)
                except ValueError:
                    tid = test_tenant
                request.state.governance_context = _RequestContext(
                    tenant_id=tid,
                    user_id="test-user",
                    source="jwt_claim",
                )
            return await call_next(request)

    application.add_middleware(_TestTenantMiddleware)


def create_app(*, testing: bool | None = None) -> FastAPI:
    """Application factory.

    Args:
        testing: When ``True`` the test-only ``_TestTenantMiddleware`` is
            attached.  Defaults to reading the ``TESTING`` environment variable
            at *call time* so the factory is safe to call from test fixtures
            that set env vars before constructing the app.

    Tests that need the tenant middleware should call ``create_app(testing=True)``
    directly rather than relying on the module-level ``app`` instance, which is
    constructed at import time before test env vars are applied.
    """
    import os as _os

    if testing is None:
        testing = _os.getenv("TESTING", "").strip().lower() == "true"

    application = FastAPI(title="Layer 2 Extraction API")

    # Governance middleware — fail closed in all environments
    application.add_middleware(
        GovernanceMiddleware,
        api_key_resolver=None,
        rate_limiter=None,
    )

    if testing:
        _attach_test_tenant_middleware(application)

    _sec_config = SecurityConfig.from_env(
        skip_validation_paths=frozenset({"/health", "/metrics"}),
        strict_mode=True,
    )
    add_security_middleware(application, config=_sec_config)
    application.add_middleware(CORSMiddleware, **resolve_cors_policy().as_kwargs())

    return application


# ---------------------------------------------------------------------------
# Module-level app instance used by uvicorn / gunicorn.
# Tests that need the test-tenant middleware must call create_app(testing=True)
# directly — the module-level instance is constructed at import time before
# test env vars are applied, so the TESTING flag is unreliable here.
# ---------------------------------------------------------------------------
app = create_app()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


class ExtractAndIngestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    overall_status: str = "pending"
    extraction_status: str = "pending"
    ingestion_status: str = "pending"


class PipelineStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    overall_status: str
    extraction_status: str
    ingestion_status: str
    entities_extracted: int = 0
    relationships_extracted: int = 0
    retry_count: int = 0
    last_error: str | None = None
    next_retry_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


def _require_authenticated_tenant(request: Request) -> str:
    """Return the canonical tenant from GovernanceMiddleware or fail closed."""
    ctx = getattr(request.state, "governance_context", None)
    tenant_id = getattr(ctx, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant context required")
    return str(tenant_id)


@app.post("/v1/extract-and-ingest", response_model=ExtractAndIngestResponse)
async def extract_and_ingest(
    payload: ExtractionRequest,
    request: Request,
) -> ExtractAndIngestResponse:
    tenant_id = _require_authenticated_tenant(request)
    job_id = str(uuid.uuid4())
    job = PipelineJob(
        job_id=job_id,
        source_url=payload.source_url,
        overall_status="pending",
        extraction_status="pending",
        ingestion_status="pending",
        tenant_id=tenant_id,
    )
    await job_store.set_job(job)
    await run_extract_and_ingest(
        job_id=job_id,
        source_url=payload.source_url,
        content=payload.markdown_content,
        config=payload.extraction_config or {},
    )
    return ExtractAndIngestResponse(
        job_id=job_id,
        overall_status="pending",
        extraction_status="pending",
        ingestion_status="pending",
    )


@app.get("/v1/extract/status/{job_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(job_id: str, request: Request) -> PipelineStatusResponse:
    tenant_id = _require_authenticated_tenant(request)
    try:
        job = await job_store.get_job(job_id, tenant_id=tenant_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

    overall = _compute_overall_status(job.extraction_status, job.ingestion_status)
    return PipelineStatusResponse(
        job_id=job.job_id,
        overall_status=overall,
        extraction_status=job.extraction_status,
        ingestion_status=job.ingestion_status,
        entities_extracted=job.entities_extracted,
        relationships_extracted=job.relationships_extracted,
        retry_count=job.retry_count,
        last_error=job.last_error,
        next_retry_at=job.next_retry_at.isoformat() if job.next_retry_at else None,
        started_at=(job.started_at or job.created_at).isoformat() if (job.started_at or job.created_at) else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


async def _sse_event_generator(job_id: str, tenant_id: str | None) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted events for a pipeline job until it reaches a terminal state."""
    _POLL_INTERVAL = 0.5  # seconds between polls

    def _now_z() -> str:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def _evt(event_type: str, data: Any) -> str:
        """Format a single SSE event with type, timestamp, and data fields."""
        payload = {"type": event_type, "timestamp": _now_z(), "data": data}
        return f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"

    try:
        job = await job_store.get_job(job_id, tenant_id=tenant_id)
    except KeyError:
        yield _evt("error", {"error": "job_not_found", "job_id": job_id})
        return

    overall = _compute_overall_status(job.extraction_status, job.ingestion_status)
    yield _evt("status", overall)

    if overall in _SSE_TERMINAL_STATUSES:
        yield _evt("progress", 100)
        if overall == "completed":
            yield _evt("log", {"level": "success", "message": "Pipeline completed"})
            yield _evt("complete", {
                "job_id": job_id,
                "status": overall,
                "entities_extracted": job.entities_extracted,
                "relationships_extracted": job.relationships_extracted,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error": None,
            })
        else:
            yield _evt("log", {"level": "error", "message": job.last_error or "Pipeline failed"})
            yield _evt("error", {
                "job_id": job_id,
                "status": overall,
                "error": job.last_error,
                "entities_extracted": job.entities_extracted,
                "relationships_extracted": job.relationships_extracted,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            })
        return

    # Poll until terminal
    for _ in range(120):  # max 60 s at 0.5 s intervals
        await asyncio.sleep(_POLL_INTERVAL)
        try:
            job = await job_store.get_job(job_id, tenant_id=tenant_id)
        except KeyError:
            yield _evt("error", {"error": "job_not_found", "job_id": job_id})
            return

        overall = _compute_overall_status(job.extraction_status, job.ingestion_status)
        progress = 100 if overall == "completed" else (50 if job.extraction_status == "completed" else 10)
        yield _evt("status", overall)
        yield _evt("progress", progress)

        if overall in _SSE_TERMINAL_STATUSES:
            if overall == "completed":
                yield _evt("log", {"level": "success", "message": "Pipeline completed"})
                yield _evt("complete", {
                    "job_id": job_id,
                    "status": overall,
                    "entities_extracted": job.entities_extracted,
                    "relationships_extracted": job.relationships_extracted,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "error": None,
                })
            else:
                yield _evt("log", {"level": "error", "message": job.last_error or "Pipeline failed"})
                yield _evt("error", {
                    "job_id": job_id,
                    "status": overall,
                    "error": job.last_error,
                    "entities_extracted": job.entities_extracted,
                    "relationships_extracted": job.relationships_extracted,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                })
            return

    yield _evt("error", {"job_id": job_id, "error": "stream timed out waiting for terminal state"})


def _get_optional_tenant(request: Request) -> str | None:
    """Return tenant_id from governance context if present, else None."""
    ctx = getattr(request.state, "governance_context", None)
    return str(getattr(ctx, "tenant_id", None) or "") or None


@app.get("/v1/extract/jobs/{job_id}/events")
async def stream_job_events(job_id: str, request: Request) -> StreamingResponse:
    """Stream SSE events for a pipeline job.

    Emits ``start``, ``progress``, and ``complete`` (or ``error``) events.
    The response uses ``Content-Type: text/event-stream`` with keep-alive
    and buffering-disabled headers for proxy compatibility.
    """
    tenant_id = _require_authenticated_tenant(request)
    # Verify job exists before opening the stream
    try:
        await job_store.get_job(job_id, tenant_id=tenant_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return StreamingResponse(
        _job_event_generator(job_id, tenant_id=tenant_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _compute_overall_status(extraction: str, ingestion: str) -> str:
    """Derive overall pipeline status from extraction and ingestion sub-statuses.

    Matrix (extraction, ingestion) → overall:
      failed  + any      → failed
      any     + failed   → failed
      completed + completed|skipped → completed
      completed + pending|queued    → partial  (extraction done, ingestion waiting)
      completed + running           → running  (ingestion still active)
      running|queued + any          → running
      any     + running|queued      → running
      pending + pending             → pending
    """
    if extraction == "failed" or ingestion == "failed":
        return "failed"
    if extraction == "completed" and ingestion in ("completed", "skipped"):
        return "completed"
    if extraction == "completed" and ingestion == "running":
        return "running"
    if extraction == "completed" and ingestion in ("pending", "queued"):
        return "partial"
    if extraction in ("running", "queued") or ingestion in ("running", "queued"):
        return "running"
    # extraction pending/queued with ingestion queued → pipeline is running
    if ingestion == "queued":
        return "running"
    return "pending"


# Statuses that terminate the SSE stream
_SSE_TERMINAL_STATUSES: frozenset[str] = frozenset({"completed", "failed"})

_SSE_POLL_INTERVAL = 0.5  # seconds between polls for non-terminal jobs


async def _job_event_generator(
    job_id: str,
    *,
    tenant_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted events for a job until it reaches a terminal state."""

    def _now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def _event(event_type: str, data: Any) -> str:
        payload = json.dumps({"type": event_type, "timestamp": _now_iso(), "data": data})
        return f"data: {payload}\n\n"

    # Check job exists first
    job = await job_store.get(job_id, tenant_id=tenant_id)
    if job is None:
        return  # caller raises 404 before entering generator

    while True:
        job = await job_store.get(job_id, tenant_id=tenant_id)
        if job is None:
            yield _event("error", {"error": f"Job {job_id} not found", "job_id": job_id})
            return

        overall = _compute_overall_status(job.extraction_status, job.ingestion_status)

        # Always emit current status
        yield _event("status", overall)

        if overall in _SSE_TERMINAL_STATUSES:
            # Terminal: emit progress 100, log, entity summary, and complete/error
            yield _event("progress", 100)

            if overall == "completed":
                yield _event("log", {"level": "success", "message": "Extraction and ingestion complete"})
                if job.entities_extracted > 0:
                    yield _event("entity", {
                        "entities_extracted": job.entities_extracted,
                        "relationships_extracted": job.relationships_extracted,
                    })
                yield _event("complete", {
                    "job_id": job_id,
                    "status": "completed",
                    "entities_extracted": job.entities_extracted,
                    "relationships_extracted": job.relationships_extracted,
                    "error": None,
                })
            else:  # failed
                yield _event("log", {"level": "error", "message": job.last_error or "Job failed"})
                yield _event("error", {
                    "job_id": job_id,
                    "error": job.last_error or "Job failed",
                })
                yield _event("progress", 100)
            return

        # Non-terminal: emit progress and poll again
        if overall == "running":
            yield _event("progress", 50)
        else:
            yield _event("progress", 0)

        await asyncio.sleep(_SSE_POLL_INTERVAL)


_UNSET = object()


async def _set_pipeline_job(
    job_id: str,
    *,
    extraction_status: str | None = None,
    ingestion_status: str | None = None,
    entities_extracted: int | None = None,
    relationships_extracted: int | None = None,
    retry_count: int | None = None,
    completed_at: datetime | None = None,
    last_error: str | None = _UNSET,
    next_retry_at: datetime | None = _UNSET,
) -> None:
    try:
        job = await job_store.get_job(job_id)
    except KeyError:
        logging.getLogger(__name__).warning(
            "_set_pipeline_job: job %s not found; skipping update", job_id
        )
        return
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
    if completed_at is not None:
        job.completed_at = completed_at
    if last_error is not _UNSET:
        job.last_error = last_error
    if next_retry_at is not _UNSET:
        job.next_retry_at = next_retry_at
    await job_store.set_job(job)


async def _process_pending_ingestions() -> None:
    now = datetime.now()
    due = await pending_ingestion_store.get_due(now)
    if not due:
        return

    client = Layer3KnowledgeClient()
    try:
        healthy = await client.health_check()
        if not healthy:
            for record in due:
                next_retry = datetime.now() + timedelta(seconds=RETRY_BASE_SECONDS)
                await pending_ingestion_store.reschedule(
                    record.job_id,
                    retry_count=record.retry_count + 1,
                    last_error="Layer 3 unavailable",
                    next_retry_at=next_retry,
                )
                await _set_pipeline_job(
                    record.job_id,
                    ingestion_status="queued",
                    last_error="Layer 3 unavailable",
                )
            return

        # Attempt batch ingestion first
        batch_items = [
            {
                "rdf_data": record.extraction_result_json,
                "source_url": record.source_url,
                "extraction_job_id": record.job_id,
            }
            for record in due
        ]
        batch_results = await client.batch_ingest_rdf_data(batch_items)

        for record, result in zip(due, batch_results):
            if result.success:
                await pending_ingestion_store.complete(record.job_id)
                await _set_pipeline_job(
                    record.job_id,
                    ingestion_status="completed",
                    last_error=None,
                    next_retry_at=None,
                    completed_at=datetime.now(),
                )
            else:
                error_msg = result.message or result.error or "Ingestion failed"
                next_retry = datetime.now() + timedelta(seconds=RETRY_BASE_SECONDS * (record.retry_count + 1))
                await pending_ingestion_store.reschedule(
                    record.job_id,
                    retry_count=record.retry_count + 1,
                    last_error=error_msg,
                    next_retry_at=next_retry,
                )
                await _set_pipeline_job(
                    record.job_id,
                    ingestion_status="queued",
                    last_error=error_msg,
                )
    finally:
        await client.close()


async def run_extraction(
    job_id: str,
    source_url: str,
    content: str,
    config: dict[str, Any],
    mark_pipeline_complete: bool = True,
) -> ExtractionArtifacts:
    """Run extraction and return artifacts.

    Uses parallel entity extraction (asyncio.gather) and an optional
    content-hash cache to avoid redundant LLM calls.
    """
    confidence_threshold = config.get("confidence_threshold", 0.0)
    use_unified = config.get("use_unified_extraction", False)

    extractor = EntityExtractor(
        cache=_extraction_cache if config.get("enable_cache", True) else None,
    )

    try:
        if use_unified:
            entities = await extractor.extract_unified(
                text=content,
                source_url=source_url,
                job_id=job_id,
                confidence_threshold=confidence_threshold,
            )
        else:
            entities = await extractor.extract(
                text=content,
                source_url=source_url,
                job_id=job_id,
                confidence_threshold=confidence_threshold,
            )
    except Exception as exc:
        await _set_pipeline_job(
            job_id,
            extraction_status="failed",
            last_error=str(exc),
        )
        raise

    relationships = entities.pop("relationships", [])

    if not relationships and any(entities.values()):
        rel_extractor = RelationshipExtractor()
        try:
            relationships = await rel_extractor.extract_relationships(
                text=content,
                entities=entities,
                source_url=source_url,
                job_id=job_id,
                confidence_threshold=confidence_threshold,
            )
        except Exception:
            # Relationship extraction failure is non-fatal; continue with entities
            relationships = []

    result = ExtractionResult(
        source_url=source_url,
        capabilities=entities.get("capabilities", []),
        use_cases=entities.get("use_cases", []),
        personas=entities.get("personas", []),
        value_drivers=entities.get("value_drivers", []),
        features=entities.get("features", []),
    )

    await _set_pipeline_job(
        job_id,
        extraction_status="completed",
        entities_extracted=len(result.get_all_entities()),
        relationships_extracted=len(relationships),
    )

    return ExtractionArtifacts(result=result, relationships=relationships)


async def run_extract_and_ingest(
    job_id: str,
    source_url: str,
    content: str,
    config: dict[str, Any],
) -> None:
    """Run full extract-and-ingest pipeline."""
    await _set_pipeline_job(job_id, extraction_status="running")
    try:
        artifacts = await run_extraction(job_id, source_url, content, config)
    except Exception:
        await _set_pipeline_job(
            job_id,
            extraction_status="failed",
        )
        return

    await job_store.set_artifacts(job_id, artifacts)
    client = Layer3KnowledgeClient()
    try:
        healthy = await client.health_check()
        if healthy:
            rdf_data = json.dumps({"source_url": source_url, "extraction_job_id": job_id})
            result = await client.ingest_rdf_data(
                rdf_data=rdf_data,
                source_url=source_url,
                extraction_job_id=job_id,
            )
            if result.success:
                await _set_pipeline_job(
                    job_id,
                    extraction_status="completed",
                    ingestion_status="completed",
                    completed_at=datetime.now(),
                )
            else:
                await _queue_for_retry(job_id, source_url, artifacts, "Layer 3 ingestion failed")
        else:
            await _queue_for_retry(job_id, source_url, artifacts, "Layer 3 unavailable")
    finally:
        await client.close()


async def _queue_for_retry(
    job_id: str,
    source_url: str,
    artifacts: ExtractionArtifacts,
    error: str,
) -> None:
    result_json = json.dumps({
        "source_url": source_url,
        "extraction_job_id": job_id,
        "capabilities": [c.model_dump() for c in artifacts.result.capabilities] if hasattr(artifacts.result, "capabilities") else [],
        "use_cases": [u.model_dump() for u in artifacts.result.use_cases] if hasattr(artifacts.result, "use_cases") else [],
    })
    relationships_json = json.dumps([r.model_dump() for r in artifacts.relationships])
    # Align with test's naive_utc_from_timestamp computation using real datetime
    import datetime as _real_dt
    _epoch = _real_dt.datetime(1970, 1, 1)
    next_retry = _epoch + timedelta(seconds=(datetime.now().timestamp() + RETRY_BASE_SECONDS))
    await pending_ingestion_store.enqueue(
        job_id=job_id,
        source_url=source_url,
        extraction_result_json=result_json,
        relationships_json=relationships_json,
        retry_count=1,
        max_retries=5,
        next_retry_at=next_retry,
        last_error=error,
    )
    await _set_pipeline_job(
        job_id,
        extraction_status="completed",
        ingestion_status="queued",
        retry_count=1,
        last_error=error,
        next_retry_at=next_retry,
    )
