"""Thin entrypoint and core endpoints for Layer 4 API."""

import time
from typing import Any

from fastapi import Request
from fastapi.responses import Response

from value_fabric.shared.models.typed_dict import TypedDictModel

from ..metrics import get_metrics
from .app_factory import create_app
from .startup import runtime_state


class health_checkResult(TypedDictModel):
    dependencies: Any
    executor_ready: bool
    metrics: dict[str, Any]
    service: str
    status: Any
    timestamp: Any
    uptime_seconds: Any
    version: str


class rootResult(TypedDictModel):
    documentation: str
    health: str
    metrics: str
    service: str
    version: str


_app_start_time = time.time()
app = create_app()


@app.get("/health")
async def health_check():
    from datetime import UTC, datetime

    import psutil

    uptime = time.time() - _app_start_time
    memory_info = psutil.virtual_memory()

    dependencies = []
    overall_status = "healthy"

    try:
        if runtime_state.checkpoint_saver is not None and getattr(runtime_state.checkpoint_saver, "conn", None):
            await runtime_state.checkpoint_saver.conn.execute("SELECT 1")
            dependencies.append({"name": "postgres", "status": "healthy", "response_time_ms": None, "error": None})
        else:
            dependencies.append({"name": "postgres", "status": "degraded", "response_time_ms": None, "error": "Checkpointing not configured"})
            overall_status = "degraded"
    except Exception as exc:
        dependencies.append({"name": "postgres", "status": "unhealthy", "response_time_ms": None, "error": str(exc)})
        overall_status = "degraded"

    try:
        if runtime_state.state_manager is not None and getattr(runtime_state.state_manager, "redis_client", None):
            await runtime_state.state_manager.redis_client.ping()
            dependencies.append({"name": "redis", "status": "healthy", "response_time_ms": None, "error": None})
        else:
            dependencies.append({"name": "redis", "status": "degraded", "response_time_ms": None, "error": "Redis not configured"})
    except Exception as exc:
        dependencies.append({"name": "redis", "status": "unhealthy", "response_time_ms": None, "error": str(exc)})

    return health_checkResult.model_validate({
        "status": overall_status,
        "service": "layer4-agents",
        "version": "0.2.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "executor_ready": runtime_state.workflow_executor is not None,
        "uptime_seconds": uptime,
        "dependencies": dependencies,
        "metrics": {
            "memory_usage_mb": memory_info.used / (1024 * 1024),
            "cpu_percent": psutil.cpu_percent(),
            "active_connections": 0,
            "total_requests": 0,
        },
    })


@app.get("/metrics")
async def metrics_endpoint(request: Request):
    metrics = getattr(request.app.state, "metrics", None)
    if not metrics:
        return Response(content="Metrics collection is disabled", status_code=503, media_type="text/plain")
    try:
        return Response(content=metrics.get_metrics(), media_type="text/plain; version=0.0.4; charset=utf-8")
    except Exception as exc:
        return Response(content=f"Error generating metrics: {exc}", status_code=500, media_type="text/plain")


@app.get("/")
async def root():
    return rootResult.model_validate({
        "service": "Layer 4: Agentic Workflow Engine",
        "version": "0.2.0",
        "documentation": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    })
