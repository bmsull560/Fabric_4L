"""Tests for job streaming SSE endpoint.

Validates Server-Sent Events endpoint for real-time job progress streaming.
"""

from datetime import datetime

import httpx
import pytest

from layer2_extraction.api import main as api_main


@pytest.fixture(autouse=True)
def reset_pipeline_state() -> None:
    """Clear pipeline jobs before each test."""
    api_main.PIPELINE_JOBS.clear()
    yield
    api_main.PIPELINE_JOBS.clear()


@pytest.fixture
async def async_client():
    """Create async HTTP client for testing."""
    transport = httpx.ASGITransport(app=api_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_sse_endpoint_returns_404_for_unknown_job(async_client):
    """SSE endpoint should return 404 for non-existent job."""
    response = await async_client.get("/extract/jobs/unknown-job/events")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_sse_endpoint_returns_streaming_response(async_client):
    """SSE endpoint should return text/event-stream content type."""
    # Create a mock job
    job_id = "test-job-123"
    api_main.PIPELINE_JOBS[job_id] = api_main.PipelineJob(
        job_id=job_id,
        extraction_status="completed",
        ingestion_status="skipped",
        overall_status="completed",
        entities_extracted=5,
        relationships_extracted=3,
        retry_count=0,
        last_error=None,
        next_retry_at=None,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )

    response = await async_client.get("/extract/jobs/test-job-123/events")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    assert response.headers["cache-control"] == "no-cache"


@pytest.mark.asyncio
async def test_sse_events_format(async_client):
    """SSE events should be properly formatted JSON with type/timestamp/data."""
    job_id = "test-job-events"
    api_main.PIPELINE_JOBS[job_id] = api_main.PipelineJob(
        job_id=job_id,
        extraction_status="completed",
        ingestion_status="skipped",
        overall_status="completed",
        entities_extracted=2,
        relationships_extracted=1,
        retry_count=0,
        last_error=None,
        next_retry_at=None,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )

    # Collect events from the stream — completed jobs emit a finite event
    # sequence (status, progress, log, complete) and then the generator exits.
    events = []
    async with async_client.stream("GET", f"/extract/jobs/{job_id}/events") as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                import json
                event_data = json.loads(line[6:])  # Strip "data: " prefix
                events.append(event_data)
                if event_data.get("type") in ("complete", "error"):
                    break

    # Verify event structure
    assert len(events) > 0
    for event in events:
        assert "type" in event
        assert "timestamp" in event
        assert "data" in event
        assert event["type"] in ["status", "progress", "log", "entity", "complete", "error"]


@pytest.mark.asyncio
async def test_sse_job_not_found(async_client):
    """SSE should handle job not found gracefully."""
    response = await async_client.get("/extract/jobs/nonexistent/events")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
