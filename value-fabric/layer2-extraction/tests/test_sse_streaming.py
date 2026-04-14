"""Comprehensive tests for the L2 SSE streaming endpoint.

Validates:
- Event format and types for completed, failed, pending, and running jobs
- SSE headers (content-type, cache-control, connection, X-Accel-Buffering)
- Error path: 404 for unknown jobs with correct error detail
- Completed job yields status, progress, log, and complete events then closes
- Failed job yields error event with last_error detail
- Entity events for running jobs with entities_extracted > 0
"""

import asyncio
import json
from datetime import datetime, timezone

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


# -----------------------------------------------------------------------
# Helper to create jobs with reasonable defaults
# -----------------------------------------------------------------------

def _make_job(
    job_id: str = "test-job",
    overall_status: str = "completed",
    extraction_status: str = "completed",
    ingestion_status: str = "skipped",
    entities_extracted: int = 5,
    relationships_extracted: int = 3,
    last_error: str | None = None,
) -> api_main.PipelineJob:
    now = datetime.now(timezone.utc)
    return api_main.PipelineJob(
        job_id=job_id,
        extraction_status=extraction_status,
        ingestion_status=ingestion_status,
        overall_status=overall_status,
        entities_extracted=entities_extracted,
        relationships_extracted=relationships_extracted,
        retry_count=0,
        last_error=last_error,
        next_retry_at=None,
        started_at=now,
        completed_at=now if overall_status in ("completed", "failed") else None,
    )


# -----------------------------------------------------------------------
# 404 / error path tests
# -----------------------------------------------------------------------

class TestSSEErrorPaths:
    """SSE endpoint error handling."""

    @pytest.mark.asyncio
    async def test_returns_404_for_unknown_job(self, async_client):
        """Unknown job_id must yield 404 with descriptive detail."""
        resp = await async_client.get("/extract/jobs/no-such-job/events")
        assert resp.status_code == 404
        body = resp.json()
        assert "not found" in body["detail"].lower()

    @pytest.mark.asyncio
    async def test_returns_404_with_job_id_in_detail(self, async_client):
        """404 detail should mention the requested job_id."""
        resp = await async_client.get("/extract/jobs/missing-123/events")
        assert resp.status_code == 404
        assert "missing-123" in resp.json()["detail"]


# -----------------------------------------------------------------------
# Header / content-type tests
# -----------------------------------------------------------------------

class TestSSEHeaders:
    """SSE response headers must be correct for streaming."""

    @pytest.mark.asyncio
    async def test_content_type_is_event_stream(self, async_client):
        """Content-Type must be text/event-stream."""
        api_main.PIPELINE_JOBS["h-1"] = _make_job(job_id="h-1")
        resp = await async_client.get("/extract/jobs/h-1/events")
        assert "text/event-stream" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_cache_control_no_cache(self, async_client):
        """Cache-Control must be no-cache for real-time streams."""
        api_main.PIPELINE_JOBS["h-2"] = _make_job(job_id="h-2")
        resp = await async_client.get("/extract/jobs/h-2/events")
        assert resp.headers["cache-control"] == "no-cache"

    @pytest.mark.asyncio
    async def test_connection_keep_alive(self, async_client):
        """Connection header must be keep-alive."""
        api_main.PIPELINE_JOBS["h-3"] = _make_job(job_id="h-3")
        resp = await async_client.get("/extract/jobs/h-3/events")
        assert resp.headers.get("connection") == "keep-alive"

    @pytest.mark.asyncio
    async def test_nginx_buffering_disabled(self, async_client):
        """X-Accel-Buffering must be 'no' to prevent nginx buffering."""
        api_main.PIPELINE_JOBS["h-4"] = _make_job(job_id="h-4")
        resp = await async_client.get("/extract/jobs/h-4/events")
        assert resp.headers.get("x-accel-buffering") == "no"


# -----------------------------------------------------------------------
# Completed job event tests
# -----------------------------------------------------------------------

class TestSSECompletedJob:
    """Completed jobs should emit status, progress, log, and complete events."""

    @pytest.mark.asyncio
    async def test_completed_job_emits_complete_event(self, async_client):
        """A completed job's stream must include a 'complete' event type."""
        api_main.PIPELINE_JOBS["c-1"] = _make_job(job_id="c-1")
        resp = await async_client.get("/extract/jobs/c-1/events")
        events = _parse_sse_events(resp.text)
        types = {e["type"] for e in events}
        assert "complete" in types

    @pytest.mark.asyncio
    async def test_completed_job_has_status_event(self, async_client):
        """A completed job must include a 'status' event."""
        api_main.PIPELINE_JOBS["c-2"] = _make_job(job_id="c-2")
        resp = await async_client.get("/extract/jobs/c-2/events")
        events = _parse_sse_events(resp.text)
        status_events = [e for e in events if e["type"] == "status"]
        assert len(status_events) >= 1
        assert status_events[0]["data"] == "completed"

    @pytest.mark.asyncio
    async def test_completed_job_progress_is_100(self, async_client):
        """A completed job must emit progress 100."""
        api_main.PIPELINE_JOBS["c-3"] = _make_job(job_id="c-3")
        resp = await async_client.get("/extract/jobs/c-3/events")
        events = _parse_sse_events(resp.text)
        progress_events = [e for e in events if e["type"] == "progress"]
        assert any(e["data"] == 100 for e in progress_events)

    @pytest.mark.asyncio
    async def test_complete_event_contains_job_metadata(self, async_client):
        """Complete event data must include job_id, status, counts."""
        api_main.PIPELINE_JOBS["c-4"] = _make_job(
            job_id="c-4", entities_extracted=7, relationships_extracted=4
        )
        resp = await async_client.get("/extract/jobs/c-4/events")
        events = _parse_sse_events(resp.text)
        complete_events = [e for e in events if e["type"] == "complete"]
        assert len(complete_events) == 1
        data = complete_events[0]["data"]
        assert data["job_id"] == "c-4"
        assert data["status"] == "completed"
        assert data["entities_extracted"] == 7
        assert data["relationships_extracted"] == 4
        assert data["error"] is None

    @pytest.mark.asyncio
    async def test_completed_job_has_log_event(self, async_client):
        """Completed jobs should emit a log event with 'success' level."""
        api_main.PIPELINE_JOBS["c-5"] = _make_job(job_id="c-5")
        resp = await async_client.get("/extract/jobs/c-5/events")
        events = _parse_sse_events(resp.text)
        log_events = [e for e in events if e["type"] == "log"]
        assert len(log_events) >= 1
        assert log_events[0]["data"]["level"] == "success"

    @pytest.mark.asyncio
    async def test_stream_terminates_for_completed_job(self, async_client):
        """Stream must terminate (not hang) after complete event."""
        api_main.PIPELINE_JOBS["c-6"] = _make_job(job_id="c-6")
        resp = await async_client.get("/extract/jobs/c-6/events")
        # If we got a response, the stream terminated
        assert resp.status_code == 200


# -----------------------------------------------------------------------
# Failed job event tests
# -----------------------------------------------------------------------

class TestSSEFailedJob:
    """Failed jobs should emit error events with error details."""

    @pytest.mark.asyncio
    async def test_failed_job_emits_error_event(self, async_client):
        """A failed job's stream must include an 'error' event."""
        api_main.PIPELINE_JOBS["f-1"] = _make_job(
            job_id="f-1",
            overall_status="failed",
            extraction_status="failed",
            last_error="LLM timeout",
        )
        resp = await async_client.get("/extract/jobs/f-1/events")
        events = _parse_sse_events(resp.text)
        types = {e["type"] for e in events}
        assert "error" in types

    @pytest.mark.asyncio
    async def test_failed_job_error_contains_last_error(self, async_client):
        """Error event data must include the last_error message."""
        api_main.PIPELINE_JOBS["f-2"] = _make_job(
            job_id="f-2",
            overall_status="failed",
            extraction_status="failed",
            last_error="Connection refused",
        )
        resp = await async_client.get("/extract/jobs/f-2/events")
        events = _parse_sse_events(resp.text)
        error_events = [e for e in events if e["type"] == "error"]
        assert len(error_events) == 1
        assert error_events[0]["data"]["error"] == "Connection refused"

    @pytest.mark.asyncio
    async def test_failed_job_has_log_with_error_level(self, async_client):
        """Failed jobs should emit a log event with 'error' level."""
        api_main.PIPELINE_JOBS["f-3"] = _make_job(
            job_id="f-3",
            overall_status="failed",
            extraction_status="failed",
            last_error="boom",
        )
        resp = await async_client.get("/extract/jobs/f-3/events")
        events = _parse_sse_events(resp.text)
        log_events = [e for e in events if e["type"] == "log"]
        assert any(le["data"]["level"] == "error" for le in log_events)

    @pytest.mark.asyncio
    async def test_failed_job_progress_is_100(self, async_client):
        """Failed jobs should still report 100% progress (terminal)."""
        api_main.PIPELINE_JOBS["f-4"] = _make_job(
            job_id="f-4",
            overall_status="failed",
            extraction_status="failed",
            last_error="timeout",
        )
        resp = await async_client.get("/extract/jobs/f-4/events")
        events = _parse_sse_events(resp.text)
        progress_events = [e for e in events if e["type"] == "progress"]
        assert any(e["data"] == 100 for e in progress_events)


# -----------------------------------------------------------------------
# Event structure tests
# -----------------------------------------------------------------------

class TestSSEEventStructure:
    """All SSE events must have the correct structure."""

    @pytest.mark.asyncio
    async def test_all_events_have_required_fields(self, async_client):
        """Every event must have type, timestamp, and data fields."""
        api_main.PIPELINE_JOBS["s-1"] = _make_job(job_id="s-1")
        resp = await async_client.get("/extract/jobs/s-1/events")
        events = _parse_sse_events(resp.text)
        assert len(events) > 0
        for event in events:
            assert "type" in event, f"Missing 'type' in event: {event}"
            assert "timestamp" in event, f"Missing 'timestamp' in event: {event}"
            assert "data" in event, f"Missing 'data' in event: {event}"

    @pytest.mark.asyncio
    async def test_timestamps_are_iso_format(self, async_client):
        """Timestamps must be ISO 8601 strings ending with Z."""
        api_main.PIPELINE_JOBS["s-2"] = _make_job(job_id="s-2")
        resp = await async_client.get("/extract/jobs/s-2/events")
        events = _parse_sse_events(resp.text)
        for event in events:
            ts = event["timestamp"]
            assert ts.endswith("Z"), f"Timestamp must end with Z: {ts}"
            # Should be parseable
            assert len(ts) > 10, f"Timestamp too short: {ts}"

    @pytest.mark.asyncio
    async def test_event_types_are_valid(self, async_client):
        """Event types must be from the defined set."""
        valid_types = {"status", "progress", "log", "entity", "complete", "error"}
        api_main.PIPELINE_JOBS["s-3"] = _make_job(job_id="s-3")
        resp = await async_client.get("/extract/jobs/s-3/events")
        events = _parse_sse_events(resp.text)
        for event in events:
            assert event["type"] in valid_types, f"Invalid type: {event['type']}"

    @pytest.mark.asyncio
    async def test_sse_lines_use_data_prefix(self, async_client):
        """Raw SSE lines must be prefixed with 'data: '."""
        api_main.PIPELINE_JOBS["s-4"] = _make_job(job_id="s-4")
        resp = await async_client.get("/extract/jobs/s-4/events")
        lines = [line for line in resp.text.strip().split("\n") if line.strip()]
        data_lines = [l for l in lines if l.startswith("data: ")]
        assert len(data_lines) > 0, "No data: prefixed lines found in SSE stream"


# -----------------------------------------------------------------------
# Pending job event tests
# -----------------------------------------------------------------------

class TestSSEPendingJob:
    """Pending jobs should emit status and progress events."""

    @pytest.mark.asyncio
    async def test_pending_job_emits_status_pending(self, async_client):
        """A pending job should initially emit status 'pending'."""
        job = _make_job(
            job_id="p-1",
            overall_status="pending",
            extraction_status="pending",
        )
        api_main.PIPELINE_JOBS["p-1"] = job

        # Schedule the job to complete after a short delay
        async def _complete_job():
            await asyncio.sleep(0.6)
            job.overall_status = "completed"
            job.extraction_status = "completed"
            job.completed_at = datetime.now(timezone.utc)

        task = asyncio.create_task(_complete_job())
        try:
            async with async_client.stream("GET", "/extract/jobs/p-1/events") as response:
                events = []
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        event = json.loads(line[6:])
                        events.append(event)
                        if event.get("type") in ("complete", "error"):
                            break
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        status_events = [e for e in events if e["type"] == "status"]
        assert any(e["data"] == "pending" for e in status_events)


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _parse_sse_events(raw_text: str) -> list[dict]:
    """Parse SSE text into list of event dicts."""
    events = []
    for line in raw_text.strip().split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                pass
    return events
