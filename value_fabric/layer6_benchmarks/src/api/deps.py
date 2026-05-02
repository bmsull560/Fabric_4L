"""Shared dependencies for Layer 6 API."""

from fastapi import Query, Request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.identity.context import RequestContext


def industry_filter(industry: str | None = Query(None, description="Filter by industry")) -> str | None:
    return industry


def segment_filter(segment: str | None = Query(None, description="Filter by segment")) -> str | None:
    return segment


# Sprint 5: RequestContext extraction for audit logging
def get_request_context(request: Request) -> "RequestContext | None":
    """Extract request context from GovernanceMiddleware if available.
    
    Used for audit logging and request identity tracking.
    Layer 6 uses minimal tenant support - identity only, no enforcement.
    """
    ctx = getattr(request.state, "context", None)
    return ctx
