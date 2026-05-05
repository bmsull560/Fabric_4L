"""Operational routes extracted from the Layer 3 monolith."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Monitoring"])


@router.get(
    "/metrics",
    include_in_schema=False,
    summary="Prometheus Metrics",
    description="Export Prometheus metrics for monitoring.",
    responses={
        200: {"description": "Prometheus metrics exported successfully"},
        503: {"description": "Metrics collection disabled"},
    },
)
async def get_metrics(request: Request) -> Response:
    """Get Prometheus metrics from the app state registry."""
    metrics = getattr(request.app.state, "metrics", None)

    if not metrics:
        return Response(
            content="Metrics collection is disabled",
            status_code=503,
            media_type="text/plain",
        )

    try:
        metrics_data = metrics.get_metrics()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )
    except Exception as exc:
        logger.error("Error generating metrics: %s", exc)
        return Response(
            content="Error generating metrics",
            status_code=500,
            media_type="text/plain",
        )

