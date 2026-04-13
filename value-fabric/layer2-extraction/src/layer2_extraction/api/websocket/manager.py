"""WebSocket connection manager for real-time pipeline streaming.

Provides pub/sub-style event broadcasting for extract-and-ingest jobs
with connection resilience, last-event-ID replay, and job-scoped channels.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """Extraction pipeline stages for progress tracking."""

    QUEUED = "queued"
    CHUNKING = "chunking"
    ENTITY_EXTRACTION = "entity_extraction"
    SEMANTIC_ALIGNMENT = "semantic_alignment"
    DEDUPLICATION = "deduplication"
    VALIDATION = "validation"
    RDF_GENERATION = "rdf_generation"
    INGESTION = "ingestion"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EventStore:
    """Ring buffer for event replay on reconnection."""

    max_events: int = 100
    events: list[dict[str, Any]] = field(default_factory=list)

    def add(self, event: dict[str, Any]) -> None:
        """Add event to buffer, maintaining max size."""
        event["_stored_at"] = datetime.utcnow().isoformat()
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events.pop(0)

    def get_since(self, last_event_id: str | None = None) -> list[dict[str, Any]]:
        """Get events since a specific event ID."""
        if not last_event_id:
            return self.events[-10:]  # Return last 10 events by default

        for i, event in enumerate(self.events):
            if event.get("event_id") == last_event_id:
                return self.events[i + 1 :]
        return []


@dataclass
class PipelineConnection:
    """Represents a WebSocket connection tracking its state."""

    websocket: WebSocket
    job_id: str
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_event_id: str | None = None
    is_alive: bool = True

    async def send_event(self, event: dict[str, Any]) -> bool:
        """Send event to this connection. Returns success status."""
        if not self.is_alive:
            return False
        try:
            await self.websocket.send_json(event)
            self.last_event_id = event.get("event_id")
            return True
        except Exception as e:
            logger.warning(f"Failed to send event to job {self.job_id}: {e}")
            self.is_alive = False
            return False


class PipelineWebSocketManager:
    """Manages WebSocket connections for pipeline streaming.

    Features:
    - Job-scoped channels (subscribe to specific pipeline events)
    - Connection resilience with automatic cleanup
    - Last-event-ID replay for reconnection recovery
    - Heartbeat/ping-pong for connection health
    - Stage-level progress tracking
    """

    def __init__(self):
        """Initialize WebSocket manager."""
        # job_id -> set of connections
        self._job_connections: dict[str, set[PipelineConnection]] = {}
        # job_id -> event history for replay
        self._event_stores: dict[str, EventStore] = {}
        # Global connection lock
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task | None = None
        self._heartbeat_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start background tasks for connection management."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("Pipeline WebSocket manager started")

    async def stop(self) -> None:
        """Stop background tasks and close all connections."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        # Close all connections gracefully
        async with self._lock:
            for job_id, connections in self._job_connections.items():
                for conn in connections:
                    try:
                        await conn.websocket.close(code=1001, reason="Server shutting down")
                    except Exception:
                        pass
            self._job_connections.clear()
            self._event_stores.clear()

        logger.info("Pipeline WebSocket manager stopped")

    async def connect(
        self, websocket: WebSocket, job_id: str, last_event_id: str | None = None
    ) -> None:
        """Accept a new WebSocket connection for a pipeline job.

        Args:
            websocket: FastAPI WebSocket instance
            job_id: Pipeline job to subscribe to
            last_event_id: Optional last seen event ID for replay
        """
        await websocket.accept()

        conn = PipelineConnection(websocket=websocket, job_id=job_id, last_event_id=last_event_id)

        async with self._lock:
            if job_id not in self._job_connections:
                self._job_connections[job_id] = set()
                self._event_stores[job_id] = EventStore()

            self._job_connections[job_id].add(conn)

        # Send missed events if reconnecting
        if last_event_id:
            missed_events = self._event_stores[job_id].get_since(last_event_id)
            for event in missed_events:
                await conn.send_event(event)

        # Send connection established event
        await conn.send_event(
            {
                "event_id": f"conn-{datetime.utcnow().timestamp()}",
                "event_type": "connection_established",
                "timestamp": datetime.utcnow().isoformat(),
                "job_id": job_id,
                "message": f"Subscribed to pipeline job {job_id}",
                "replay_count": len(missed_events) if last_event_id else 0,
            }
        )

        logger.info(f"WebSocket connected for pipeline job {job_id}")

    async def disconnect(self, websocket: WebSocket, job_id: str) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if job_id in self._job_connections:
                # Find and remove the connection
                conn_to_remove = None
                for conn in self._job_connections[job_id]:
                    if conn.websocket == websocket:
                        conn_to_remove = conn
                        break

                if conn_to_remove:
                    conn_to_remove.is_alive = False
                    self._job_connections[job_id].discard(conn_to_remove)

                    # Cleanup if no more connections for this job
                    if not self._job_connections[job_id]:
                        del self._job_connections[job_id]
                        del self._event_stores[job_id]

        logger.info(f"WebSocket disconnected for pipeline job {job_id}")

    async def broadcast_to_job(
        self, job_id: str, event_type: str, payload: dict[str, Any], message: str | None = None
    ) -> int:
        """Broadcast an event to all connections for a job.

        Returns:
            Number of successful deliveries
        """
        event = {
            "event_id": f"evt-{datetime.utcnow().timestamp()}-{id(payload)}",
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "job_id": job_id,
            "message": message or event_type,
            "payload": payload,
        }

        # Store for replay
        async with self._lock:
            if job_id in self._event_stores:
                self._event_stores[job_id].add(event)

        # Broadcast to all connections
        delivered = 0
        dead_connections = []

        async with self._lock:
            if job_id not in self._job_connections:
                return 0

            connections = list(self._job_connections[job_id])

        for conn in connections:
            success = await conn.send_event(event)
            if success:
                delivered += 1
            else:
                dead_connections.append(conn)

        # Cleanup dead connections
        if dead_connections:
            async with self._lock:
                if job_id in self._job_connections:
                    for conn in dead_connections:
                        self._job_connections[job_id].discard(conn)

        return delivered

    async def broadcast_stage_start(
        self,
        job_id: str,
        stage: PipelineStage,
        stage_number: int,
        total_stages: int = 6,
        metadata: dict | None = None,
    ) -> int:
        """Broadcast pipeline stage start event."""
        payload = {
            "stage": stage.value,
            "stage_number": stage_number,
            "total_stages": total_stages,
            "progress_percent": int((stage_number - 1) / total_stages * 100),
            "status": "running",
            "metadata": metadata or {},
        }

        return await self.broadcast_to_job(
            job_id=job_id,
            event_type="stage_start",
            payload=payload,
            message=f"Starting stage {stage_number}/{total_stages}: {stage.value}",
        )

    async def broadcast_stage_progress(
        self,
        job_id: str,
        stage: PipelineStage,
        stage_number: int,
        total_stages: int = 6,
        items_processed: int = 0,
        items_total: int = 0,
        stage_percent: int = 0,
        metadata: dict | None = None,
    ) -> int:
        """Broadcast pipeline stage progress update."""
        overall_percent = int(((stage_number - 1) + stage_percent / 100) / total_stages * 100)

        payload = {
            "stage": stage.value,
            "stage_number": stage_number,
            "total_stages": total_stages,
            "items_processed": items_processed,
            "items_total": items_total,
            "stage_percent": stage_percent,
            "overall_percent": overall_percent,
            "status": "running",
            "metadata": metadata or {},
        }

        return await self.broadcast_to_job(
            job_id=job_id,
            event_type="stage_progress",
            payload=payload,
            message=f"Stage {stage.value}: {stage_percent}% ({items_processed}/{items_total})",
        )

    async def broadcast_stage_complete(
        self,
        job_id: str,
        stage: PipelineStage,
        stage_number: int,
        total_stages: int = 6,
        result_summary: dict | None = None,
    ) -> int:
        """Broadcast pipeline stage completion."""
        progress_percent = int(stage_number / total_stages * 100)

        payload = {
            "stage": stage.value,
            "stage_number": stage_number,
            "total_stages": total_stages,
            "progress_percent": progress_percent,
            "status": "completed",
            "result_summary": result_summary or {},
        }

        return await self.broadcast_to_job(
            job_id=job_id,
            event_type="stage_complete",
            payload=payload,
            message=f"Completed stage {stage_number}/{total_stages}: {stage.value}",
        )

    async def broadcast_ingestion_status(
        self,
        job_id: str,
        status: str,  # "queued", "retrying", "running", "completed", "failed"
        retry_count: int = 0,
        max_retries: int = 3,
        entities_loaded: int | None = None,
        relationships_loaded: int | None = None,
        error: str | None = None,
    ) -> int:
        """Broadcast ingestion status update."""
        payload = {
            "stage": "ingestion",
            "ingestion_status": status,
            "retry_count": retry_count,
            "max_retries": max_retries,
            "entities_loaded": entities_loaded,
            "relationships_loaded": relationships_loaded,
            "error": error,
        }

        return await self.broadcast_to_job(
            job_id=job_id,
            event_type="ingestion_status",
            payload=payload,
            message=f"Ingestion {status}"
            + (f" (retry {retry_count}/{max_retries})" if retry_count > 0 else ""),
        )

    async def broadcast_pipeline_complete(
        self,
        job_id: str,
        status: str,  # "completed", "partial", "failed"
        entities_extracted: int = 0,
        relationships_extracted: int = 0,
        entities_loaded: int | None = None,
        relationships_loaded: int | None = None,
        errors: list[str] | None = None,
        rdf_path: str | None = None,
    ) -> int:
        """Broadcast pipeline completion event."""
        payload = {
            "status": status,
            "entities_extracted": entities_extracted,
            "relationships_extracted": relationships_extracted,
            "entities_loaded": entities_loaded,
            "relationships_loaded": relationships_loaded,
            "errors": errors or [],
            "rdf_path": rdf_path,
            "completion_time": datetime.utcnow().isoformat(),
        }

        return await self.broadcast_to_job(
            job_id=job_id,
            event_type="pipeline_complete",
            payload=payload,
            message=f"Pipeline {status}",
        )

    async def broadcast_error(
        self, job_id: str, stage: PipelineStage, error: str, recoverable: bool = False
    ) -> int:
        """Broadcast pipeline error event."""
        payload = {
            "stage": stage.value,
            "error": error,
            "recoverable": recoverable,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return await self.broadcast_to_job(
            job_id=job_id,
            event_type="error",
            payload=payload,
            message=f"Error in {stage.value}: {error[:100]}",
        )

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of stale connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._cleanup_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_stale_connections(self) -> None:
        """Remove connections that haven't responded."""
        stale_threshold = timedelta(minutes=5)
        now = datetime.utcnow()
        dead_connections = []

        async with self._lock:
            for job_id, connections in self._job_connections.items():
                for conn in connections:
                    if now - conn.connected_at > stale_threshold and not conn.is_alive:
                        dead_connections.append((job_id, conn))

        for job_id, conn in dead_connections:
            await self.disconnect(conn.websocket, job_id)
            logger.debug(f"Cleaned up stale connection for job {job_id}")

    async def _heartbeat_loop(self) -> None:
        """Send periodic pings to keep connections alive."""
        while True:
            try:
                await asyncio.sleep(30)  # Ping every 30 seconds
                await self._send_heartbeats()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    async def _send_heartbeats(self) -> None:
        """Send ping to all connections and check health."""
        dead_connections = []

        async with self._lock:
            for job_id, connections in self._job_connections.items():
                for conn in connections:
                    try:
                        await conn.websocket.send_json(
                            {"event_type": "ping", "timestamp": datetime.utcnow().isoformat()}
                        )
                    except Exception:
                        conn.is_alive = False
                        dead_connections.append((job_id, conn))

        # Cleanup dead connections
        for job_id, conn in dead_connections:
            await self.disconnect(conn.websocket, job_id)

    async def handle_client_message(
        self, websocket: WebSocket, job_id: str, message: dict[str, Any]
    ) -> None:
        """Handle messages from client (acknowledgments, ping responses, etc.)."""
        msg_type = message.get("type")

        if msg_type == "pong":
            # Client responded to ping, mark connection alive
            async with self._lock:
                if job_id in self._job_connections:
                    for conn in self._job_connections[job_id]:
                        if conn.websocket == websocket:
                            conn.is_alive = True
                            break

        elif msg_type == "ack":
            # Client acknowledged event receipt
            event_id = message.get("event_id")
            logger.debug(f"Client acknowledged event {event_id} for job {job_id}")

        elif msg_type == "subscribe_history":
            # Client requesting full history
            events = self._event_stores.get(job_id, EventStore()).events
            await websocket.send_json(
                {
                    "event_type": "history_response",
                    "events": events[-50:],  # Send last 50 events
                }
            )


# Global singleton instance
_ws_manager: PipelineWebSocketManager | None = None


def get_pipeline_ws_manager() -> PipelineWebSocketManager:
    """Get or create the global WebSocket manager instance."""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = PipelineWebSocketManager()
    return _ws_manager
