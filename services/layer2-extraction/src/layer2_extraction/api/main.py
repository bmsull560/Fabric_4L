"""Layer 2 extraction API main module."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from layer2_extraction.integration.job_store import (
    ExtractionArtifacts,
    InMemoryJobStore,
    PipelineJob,
    build_job_store,
)
from layer2_extraction.integration.layer3_client import Layer3KnowledgeClient
from layer2_extraction.integration.pending_ingestion_store import (
    InMemoryPendingIngestionStore,
    PendingIngestionRecord,
    build_pending_ingestion_store,
)
from layer2_extraction.models.extraction_api import ExtractionRequest, ExtractionResult


RETRY_BASE_SECONDS = 60

job_store = InMemoryJobStore()
pending_ingestion_store = InMemoryPendingIngestionStore()

app = FastAPI(title="Layer 2 Extraction API")


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


@app.post("/v1/extract-and-ingest", response_model=ExtractAndIngestResponse)
async def extract_and_ingest(payload: ExtractionRequest) -> ExtractAndIngestResponse:
    job_id = str(uuid.uuid4())
    job = PipelineJob(
        job_id=job_id,
        source_url=payload.source_url,
        overall_status="pending",
        extraction_status="pending",
        ingestion_status="pending",
    )
    await job_store.set_job(job)
    return ExtractAndIngestResponse(
        job_id=job_id,
        overall_status="pending",
        extraction_status="pending",
        ingestion_status="pending",
    )


@app.get("/v1/extract/status/{job_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(job_id: str) -> PipelineStatusResponse:
    try:
        job = await job_store.get_job(job_id)
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
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


def _compute_overall_status(extraction: str, ingestion: str) -> str:
    if extraction == "failed" or ingestion == "failed":
        return "failed"
    if extraction == "completed" and ingestion == "completed":
        return "completed"
    if extraction == "completed" and ingestion != "completed":
        return "partial"
    if extraction == "running" or ingestion == "running":
        return "running"
    return "pending"


async def _set_pipeline_job(
    job_id: str,
    *,
    extraction_status: str | None = None,
    ingestion_status: str | None = None,
    entities_extracted: int | None = None,
    relationships_extracted: int | None = None,
    completed_at: datetime | None = None,
    last_error: str | None = None,
    next_retry_at: datetime | None = None,
) -> None:
    job = await job_store.get_job(job_id)
    if extraction_status is not None:
        job.extraction_status = extraction_status
    if ingestion_status is not None:
        job.ingestion_status = ingestion_status
    if entities_extracted is not None:
        job.entities_extracted = entities_extracted
    if relationships_extracted is not None:
        job.relationships_extracted = relationships_extracted
    if completed_at is not None:
        job.completed_at = completed_at
    if last_error is not None:
        job.last_error = last_error
    if next_retry_at is not None:
        job.next_retry_at = next_retry_at
    await job_store.set_job(job)


async def _process_pending_ingestions() -> None:
    now = datetime.utcnow()
    due = await pending_ingestion_store.get_due(now)
    for record in due:
        client = Layer3KnowledgeClient()
        healthy = await client.health_check()
        if healthy:
            try:
                result = await client.ingest_rdf_data(
                    rdf_data=record.extraction_result_json,
                    source_url=record.source_url,
                    extraction_job_id=record.job_id,
                )
                if result.success:
                    await pending_ingestion_store.complete(record.job_id)
                    await _set_pipeline_job(
                        record.job_id,
                        ingestion_status="completed",
                        completed_at=datetime.utcnow(),
                    )
                else:
                    raise RuntimeError(result.message or "Ingestion failed")
            except Exception as exc:
                next_retry = datetime.utcnow() + timedelta(seconds=RETRY_BASE_SECONDS * (record.retry_count + 1))
                await pending_ingestion_store.reschedule(
                    record.job_id,
                    retry_count=record.retry_count + 1,
                    last_error=str(exc),
                    next_retry_at=next_retry,
                )
                await _set_pipeline_job(
                    record.job_id,
                    ingestion_status="queued",
                    last_error=str(exc),
                )
        else:
            next_retry = datetime.utcnow() + timedelta(seconds=RETRY_BASE_SECONDS)
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


async def run_extraction(
    job_id: str,
    source_url: str,
    content: str,
    config: dict[str, Any],
    mark_pipeline_complete: bool = True,
) -> ExtractionArtifacts:
    """Run extraction and return artifacts."""
    result = ExtractionResult(source_url=source_url)
    return ExtractionArtifacts(result=result, relationships=[])


async def run_extract_and_ingest(
    job_id: str,
    source_url: str,
    content: str,
    config: dict[str, Any],
) -> None:
    """Run full extract-and-ingest pipeline."""
    artifacts = await run_extraction(job_id, source_url, content, config)
    await job_store.set_artifacts(job_id, artifacts)
    client = Layer3KnowledgeClient()
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
                completed_at=datetime.utcnow(),
            )
        else:
            await _queue_for_retry(job_id, source_url, artifacts, "Layer 3 ingestion failed")
    else:
        await _queue_for_retry(job_id, source_url, artifacts, "Layer 3 unavailable")


async def _queue_for_retry(
    job_id: str,
    source_url: str,
    artifacts: ExtractionArtifacts,
    error: str,
) -> None:
    result_json = json.dumps({"source_url": source_url})
    relationships_json = json.dumps([])
    next_retry = datetime.utcnow() + timedelta(seconds=RETRY_BASE_SECONDS)
    await pending_ingestion_store.enqueue(
        job_id=job_id,
        source_url=source_url,
        extraction_result_json=result_json,
        relationships_json=relationships_json,
        retry_count=1,
        next_retry_at=next_retry,
        last_error=error,
    )
    await _set_pipeline_job(
        job_id,
        extraction_status="completed",
        ingestion_status="queued",
        last_error=error,
        next_retry_at=next_retry,
    )
