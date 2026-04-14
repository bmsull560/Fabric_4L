"""Extraction job routes for Layer 2 API."""

from fastapi import APIRouter, BackgroundTasks

from .. import main as handlers

router = APIRouter(prefix="/v1", tags=["extraction"])


@router.post("/extract", response_model=handlers.ExtractResponse)
async def extract(request: handlers.ExtractRequest, background_tasks: BackgroundTasks):
    return await handlers.extract(request, background_tasks)


@router.post("/extract-and-ingest", response_model=handlers.ExtractAndIngestResponse)
async def extract_and_ingest(request: handlers.ExtractRequest, background_tasks: BackgroundTasks):
    return await handlers.extract_and_ingest(request, background_tasks)


@router.get("/extract/status/{job_id}", response_model=handlers.ExtractionStatusResponse)
async def get_extraction_status(job_id: str):
    return await handlers.get_extraction_status(job_id)


@router.post("/extract/batch")
async def extract_batch(requests: list[handlers.ExtractRequest], background_tasks: BackgroundTasks):
    return await handlers.extract_batch(requests, background_tasks)


@router.get("/extract/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    return await handlers.stream_job_events(job_id)
