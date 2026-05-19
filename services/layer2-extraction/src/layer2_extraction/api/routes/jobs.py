"""Job and streaming routes for Layer 2 API."""

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel

from .. import service

router = APIRouter(prefix="/v1", tags=["jobs"])


class IngestionCompletedWebhook(BaseModel):
    """Payload from L1 outbox dispatcher notifying L2 that ingestion finished."""
    tenant_id: str
    job_id: str
    target_id: str
    status: str
    output_url: str | None = None
    metadata: dict = {}


@router.get("/extract/status/{job_id}", response_model=service.ExtractionStatusResponse)
async def get_extraction_status(job_id: str):
    return await service.get_extraction_status(job_id)


@router.post("/extract/batch")
async def extract_batch(requests: list[service.ExtractRequest], background_tasks: BackgroundTasks):
    return await service.extract_batch(requests, background_tasks)


@router.get("/extract/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    return await service.stream_job_events(job_id)


@router.post("/webhooks/ingestion-completed")
async def ingestion_completed_webhook(body: IngestionCompletedWebhook, request: Request):
    """Receive notification from L1 that an ingestion job completed.

    Triggers L2 extraction pipeline for the ingested content.
    """
    # Delegate to service layer to enqueue extraction
    return await service.handle_ingestion_completed(body.model_dump())
