"""Operational routes extracted from the Layer 3 monolith."""

from __future__ import annotations

import logging
import platform
import time
from datetime import UTC, datetime
from typing import Any, Literal, cast

import psutil  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from value_fabric.layer3.config import get_settings

from ..shared_bootstrap import verify_metrics_access
from ..dependencies import get_schema_initializer, recover_neo4j_state
from ..models import (
    DependencyStatus,
    DetailedHealthResponse,
    HealthResponse,
    ServiceMetrics,
)

logger = logging.getLogger(__name__)

router = APIRouter()
_app_metrics: Any | None = None
_app_start_time = time.time()


def set_app_metrics(metrics: Any | None) -> None:
    """Set the global metrics instance for health check access."""
    global _app_metrics
    _app_metrics = metrics


async def check_dependencies(schema_initializer: Any | None = None) -> list[DependencyStatus]:
    """Check health of Layer 3 dependencies."""
    dependencies: list[DependencyStatus] = []
    settings = get_settings()

    try:
        if schema_initializer is not None and getattr(schema_initializer, "_driver", None) is None:
            dependencies.append(
                DependencyStatus(
                    name="neo4j",
                    status="degraded",
                    response_time_ms=None,
                    error="Neo4j not initialized",
                    details={
                        "uri": settings.neo4j_uri,
                        "database": settings.neo4j_database,
                    },
                )
            )
        else:
            from ...schema.initializer import SchemaInitializer

            neo4j_checker = (
                schema_initializer if schema_initializer is not None else SchemaInitializer()
            )
            if schema_initializer is None:
                neo4j_checker._owned_driver = False
            start_time = time.time()
            neo4j_health = await neo4j_checker.health_check()
            response_time = (time.time() - start_time) * 1000

            dependencies.append(
                DependencyStatus(
                    name="neo4j",
                    status=neo4j_health["status"],
                    response_time_ms=response_time,
                    error=neo4j_health.get("error"),
                    details={
                        "uri": settings.neo4j_uri,
                        "database": settings.neo4j_database,
                    },
                )
            )
    except Exception as exc:
        dependencies.append(
            DependencyStatus(
                name="neo4j",
                status="unhealthy",
                response_time_ms=None,
                error=str(exc),
                details={"uri": settings.neo4j_uri},
            )
        )

    if settings.pinecone_api_key:
        try:
            start_time = time.time()
            response_time = (time.time() - start_time) * 1000
            dependencies.append(
                DependencyStatus(
                    name="pinecone",
                    status="healthy",
                    response_time_ms=response_time,
                    error=None,
                    details={"index": settings.pinecone_index},
                )
            )
        except Exception as exc:
            dependencies.append(
                DependencyStatus(
                    name="pinecone",
                    status="unhealthy",
                    response_time_ms=None,
                    error=str(exc),
                )
            )

    return dependencies


def get_system_metrics() -> ServiceMetrics:
    """Collect system and application metrics from Prometheus."""
    uptime = time.time() - _app_start_time
    memory_info = psutil.virtual_memory()
    memory_usage_mb = memory_info.used / (1024 * 1024)
    cpu_percent = psutil.cpu_percent(interval=None)

    total_requests = 0
    total_errors = 0
    active_connections = 0
    error_rate_percent = 0.0

    if _app_metrics is not None:
        try:
            registry = _app_metrics.config.registry
            prefix = _app_metrics.config.prefix

            for metric in registry.collect():
                if metric.name == f"{prefix}active_connections":
                    for sample in metric.samples:
                        if sample.labels.get("connection_type") == "total":
                            active_connections = int(sample.value)
                            break
                elif metric.name == f"{prefix}http_requests_total":
                    for sample in metric.samples:
                        total_requests += int(sample.value)
                elif metric.name == f"{prefix}errors_total":
                    for sample in metric.samples:
                        total_errors += int(sample.value)

            if total_requests > 0:
                error_rate_percent = round((total_errors / total_requests) * 100, 2)
        except Exception as exc:
            logger.warning("Failed to extract Prometheus metrics: %s", exc)

    return ServiceMetrics(
        uptime_seconds=uptime,
        memory_usage_mb=round(memory_usage_mb, 2),
        cpu_percent=round(cpu_percent, 2),
        active_connections=active_connections,
        total_requests=total_requests,
        error_rate_percent=error_rate_percent,
    )


def _derive_overall_status(
    dependencies: list[DependencyStatus],
    schema_initializer: Any | None,
) -> Literal["healthy", "unhealthy", "degraded"]:
    if schema_initializer is None or getattr(schema_initializer, "_driver", None) is None:
        return "degraded"
    if any(dep.status == "unhealthy" for dep in dependencies):
        return "unhealthy"
    if any(dep.status == "degraded" for dep in dependencies):
        return "degraded"
    return "healthy"


@router.get(
    "/metrics",
    tags=["Monitoring"],
    include_in_schema=False,
    summary="Prometheus Metrics",
    description="Export Prometheus metrics for monitoring.",
    responses={
        403: {"description": "Metrics endpoint requires internal access"},
        200: {"description": "Prometheus metrics exported successfully"},
        503: {"description": "Metrics collection disabled"},
    },
)
async def get_metrics(request: Request) -> Response:
    """Get Prometheus metrics from the app state registry."""
    if not verify_metrics_access(request):
        raise HTTPException(status_code=403, detail="Metrics endpoint requires internal access")

    metrics = getattr(request.app.state, "metrics", None)

    if not metrics:
        return Response(
            content="# Metrics collection is disabled",
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
            content=f"# Error: {exc}",
            status_code=500,
            media_type="text/plain",
        )


@router.get("/health", response_model=HealthResponse, tags=["Health"], summary="Basic Health Check")
async def health_check(
    request: Request,
    schema_initializer: Any = Depends(get_schema_initializer),
) -> dict[str, Any]:
    """Check service health and Neo4j connectivity."""
    start_time = time.time()
    request_id = getattr(request.state, "request_id", "unknown")
    if schema_initializer is None or getattr(schema_initializer, "_driver", None) is None:
        recovered_state = await recover_neo4j_state(request.app)
        schema_initializer = recovered_state.schema_initializer
    dependencies = await check_dependencies(schema_initializer=schema_initializer)
    metrics = get_system_metrics()

    neo4j_health: dict[str, Any] = {"status": "unavailable", "message": "Neo4j not initialized"}
    schema_status: dict[str, Any] = {"status": "unknown", "message": "Schema initializer not available"}

    if schema_initializer is not None:
        try:
            if getattr(schema_initializer, "_driver", None) is None:
                schema_status = {
                    "status": "degraded",
                    "message": "Schema initializer has no Neo4j driver",
                }
            else:
                health_result = await schema_initializer.health_check()
                neo4j_health = (
                    health_result.model_dump() if hasattr(health_result, "model_dump") else dict(health_result)
                )
                schema_status = await schema_initializer.verify_schema()
        except Exception:
            logger.warning(
                "Health check failed for Neo4j",
                exc_info=True,
                extra={"health_request_id": request_id},
            )
            neo4j_health = {"status": "error", "message": "Neo4j health check failed"}
            schema_status = {"status": "error", "message": "Neo4j health check failed"}

    overall_status = _derive_overall_status(dependencies, schema_initializer)
    response_time_ms = round((time.time() - start_time) * 1000, 2)

    logger.info(
        "Health check completed",
        extra={
            "health_request_id": request_id,
            "status": overall_status,
            "response_time_ms": response_time_ms,
            "neo4j_status": neo4j_health.get("status"),
        },
    )

    return {
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": datetime.now(UTC),
        "uptime_seconds": metrics.uptime_seconds,
        "response_time_ms": response_time_ms,
        "dependencies": dependencies,
        "metrics": metrics,
        "neo4j": neo4j_health,
        "schema_status": schema_status,
    }


@router.get(
    "/health/detailed",
    response_model=DetailedHealthResponse,
    tags=["Health"],
    summary="Detailed Health Check",
)
async def detailed_health_check(
    request: Request,
    schema_initializer: Any = Depends(get_schema_initializer),
) -> DetailedHealthResponse:
    """Get detailed health information with system info and configuration."""
    if schema_initializer is None or getattr(schema_initializer, "_driver", None) is None:
        recovered_state = await recover_neo4j_state(request.app)
        schema_initializer = recovered_state.schema_initializer
    dependencies = await check_dependencies(schema_initializer=schema_initializer)
    metrics = get_system_metrics()

    if schema_initializer is None or getattr(schema_initializer, "_driver", None) is None:
        neo4j_health: dict[str, Any] = {"status": "unavailable", "message": "Neo4j not initialized"}
        schema_status: dict[str, Any] = {
            "status": "degraded",
            "message": "Schema initializer has no Neo4j driver",
        }
    else:
        health_result = await schema_initializer.health_check()
        neo4j_health = (
            health_result.model_dump() if hasattr(health_result, "model_dump") else dict(health_result)
        )
        schema_status = await schema_initializer.verify_schema()

    overall_status = cast(
        Literal["healthy", "unhealthy", "degraded"],
        _derive_overall_status(dependencies, schema_initializer),
    )

    settings = get_settings()
    system_info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": psutil.virtual_memory().total / (1024**3),
        "disk_usage_gb": psutil.disk_usage("/").used / (1024**3),
    }
    configuration = {
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "log_level": settings.log_level,
        "log_format": settings.log_format,
        "neo4j_database": settings.neo4j_database,
        "neo4j_max_pool_size": settings.neo4j_max_pool_size,
        "pinecone_configured": bool(settings.pinecone_api_key),
    }

    return DetailedHealthResponse(
        status=overall_status,
        version="1.0.0",
        timestamp=datetime.now(UTC),
        uptime_seconds=metrics.uptime_seconds,
        dependencies=dependencies,
        metrics=metrics,
        neo4j=neo4j_health,
        schema_status=schema_status,
        system_info=system_info,
        configuration=configuration,
    )

