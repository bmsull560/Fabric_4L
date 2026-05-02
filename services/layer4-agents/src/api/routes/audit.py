"""Audit logs API routes - L3 proxy/stub for development.

This module provides a stub implementation of the L3 audit logs endpoint
for use in local development where only L4 is running.
"""

from typing import Any, Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogEntry(BaseModel):
    """Single audit log entry."""
    id: str
    timestamp: str
    source: Literal["provenance", "access_log"]
    event_type: str
    entity_id: str | None = None
    entity_type: str | None = None
    action: str
    agent: str
    details: dict[str, Any]


class AuditLogResponse(BaseModel):
    """Audit log query response."""
    entries: list[AuditLogEntry]
    total: int
    page: int
    per_page: int


@router.get("/logs", response_model=AuditLogResponse)
async def list_audit_logs(
    source: Literal["provenance", "access", "all"] | None = Query(None, description="Filter by log source"),
    from_date: str | None = Query(None, description="Start date (ISO format)"),
    to_date: str | None = Query(None, description="End date (ISO format)"),
    entity_type: str | None = Query(None, description="Filter by entity type"),
    event_type: str | None = Query(None, description="Filter by event type"),
    agent: str | None = Query(None, description="Filter by agent/user"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
) -> AuditLogResponse:
    """Query system audit events.

    This is a stub implementation that returns empty results for local development.
    In production, this endpoint would query Neo4j provenance or API access logs.

    **Query Parameters:**
    - `source`: Filter by source - 'provenance', 'access', or 'all'
    - `from_date`: Start date filter (ISO format)
    - `to_date`: End date filter (ISO format)
    - `entity_type`: Filter by entity type
    - `event_type`: Filter by event type
    - `agent`: Filter by agent/user identifier
    - `page`: Page number for pagination (default: 1)
    - `per_page`: Items per page (default: 20, max: 100)

    **Returns:**
    - `entries`: List of matching audit log entries
    - `total`: Total count of matching entries
    - `page`: Current page number
    - `per_page`: Items per page
    """
    # Stub implementation - returns empty results for local dev
    return AuditLogResponse(
        entries=[],
        total=0,
        page=page,
        per_page=per_page,
    )
