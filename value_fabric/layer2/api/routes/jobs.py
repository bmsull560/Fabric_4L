"""Job and streaming routes for Layer 2 API."""

from fastapi import APIRouter, BackgroundTasks

from .. import service

router = APIRouter(prefix="/v1", tags=["jobs"])


@router.get("/extract/status/{job_id}", response_model=service.ExtractionStatusResponse)
async def get_extraction_status(job_id: str):
    return await service.get_extraction_status(job_id)


@router.post("/extract/batch")
async def extract_batch(requests: list[service.ExtractRequest], background_tasks: BackgroundTasks):
    return await service.extract_batch(requests, background_tasks)


@router.get("/extract/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    return await service.stream_job_events(job_id)
