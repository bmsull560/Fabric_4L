"""Layer 6 Benchmark Service - FastAPI main application.

Standalone service on port 8006 for comparative intelligence.
P1-29: OpenTelemetry tracing integration for observability.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

# Logger defined early so lifespan() and module-level instrumentation can use it.
logger = logging.getLogger(__name__)

try:
    from value_fabric.shared.secrets import load_infisical_secrets
    load_infisical_secrets()
except ImportError:
    pass  # shared package not available; env vars used directly

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import Response

from value_fabric.shared.identity.context import RequestContext, get_request_context

from ..shared_bootstrap import (
    SecurityConfig,
    add_security_middleware,
    build_health_response,
    create_fabric_app,
    install_metrics_middleware,
    register_health_endpoint,
    resolve_cors_policy,
    validate_production_safety,
    verify_metrics_access,
)

from ..database import close_driver, get_driver
from ..database import health_check as neo4j_health_check
from ..metrics import MetricsMiddleware, get_metrics, initialize_metrics
from ..models.benchmark_dataset import (
    FINANCIAL_SERVICES_BENCHMARK_SEED,
    HEALTHCARE_BENCHMARK_SEED,
    MANUFACTURING_BENCHMARK_SEED,
    SAAS_B2B_BENCHMARK_SEED,
    BenchmarkDataset,
    BenchmarkMetric,
    StatisticalProfile,
)
from ..repositories.benchmark_repository import BenchmarkRepository
from .routes import benchmarks, system

# Neo4j-backed repository (initialized in lifespan)
_benchmark_repo: BenchmarkRepository | None = None
_neo4j_startup_error: str | None = None


def _build_dataset_from_seed(seed: dict) -> BenchmarkDataset:
    """Construct a BenchmarkDataset from a seed dict."""
    dataset = BenchmarkDataset(
        dataset_id=seed["dataset_id"],
        name=seed["name"],
        description=seed["description"],
        industry=seed["industry"],
        segment=seed["segment"],
        geography=seed["geography"],
        version=seed["version"],
        data_source=seed["data_source"],
        is_public=seed["is_public"],
    )

    for metric_data in seed["metrics"].values():
        profile = StatisticalProfile.from_dict(metric_data["profile"])
        metric = BenchmarkMetric(
            name=metric_data["name"],
            unit=metric_data["unit"],
            description=metric_data["description"],
            profile=profile,
            lower_bound=Decimal(metric_data.get("lower_bound", "0"))
            if "lower_bound" in metric_data
            else None,
            upper_bound=Decimal(metric_data.get("upper_bound", "0"))
            if "upper_bound" in metric_data
            else None,
            is_higher_better=metric_data.get("is_higher_better", True),
        )
        dataset.add_metric(metric)

    return dataset


async def _init_seed_data():
    """Initialize with all benchmark reference datasets."""
    seeds = [
        MANUFACTURING_BENCHMARK_SEED,
        SAAS_B2B_BENCHMARK_SEED,
        HEALTHCARE_BENCHMARK_SEED,
        FINANCIAL_SERVICES_BENCHMARK_SEED,
    ]

    if _benchmark_repo is not None:
        for seed in seeds:
            dataset = _build_dataset_from_seed(seed)
            await _benchmark_repo.save_dataset(dataset)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    validate_production_safety()

    if app.state.telemetry_provider is not None:
        logger.info("L6: OpenTelemetry tracing initialized")

    metrics = getattr(app.state, "metrics", None)
    if metrics:
        logger.info("Prometheus metrics initialized")

    # Startup: initialize Neo4j and seed data. Neo4j can be slow to accept
    # Bolt connections in constrained release-smoke environments even after the
    # HTTP health endpoint reports healthy. Keep the API process alive in a
    # degraded state so Docker Compose readiness and explicit service probes can
    # observe the service instead of treating a transient graph-store delay as a
    # process crash. Request handlers that need benchmarks still return 503 while
    # the repository is unavailable.
    global _benchmark_repo, _neo4j_startup_error
    dataset_count = 0
    try:
        driver = await get_driver()
        _benchmark_repo = BenchmarkRepository(driver)
        await _init_seed_data()
        datasets = await _benchmark_repo.list_datasets(tenant_id="system")
        dataset_count = len(datasets)
        _neo4j_startup_error = None
        logger.info("Layer 6 Benchmark Service started with %d datasets", dataset_count)
    except Exception as exc:
        _benchmark_repo = None
        _neo4j_startup_error = str(exc)
        logger.warning(
            "Layer 6 Benchmark Service starting degraded; Neo4j benchmark store unavailable: %s",
            exc,
        )

    if metrics:
        metrics.set_datasets_loaded(dataset_count)
    yield
    # Shutdown
    await close_driver()
    _benchmark_repo = None


app = create_fabric_app(
    service_name="layer6-benchmarks",
    title="Value Fabric - Benchmark Service",
    description="Comparative intelligence and peer benchmarking API",
    version="1.0.0",
    lifespan=lifespan,
    cors_policy=resolve_cors_policy(),
    telemetry_service_name="layer6-benchmarks",
    instrument_telemetry=True,
)

if app.state.telemetry_provider is not None:
    logger.info("L6: FastAPI instrumented with OpenTelemetry")

# Initialize Prometheus metrics and middleware at module level (before app starts)
install_metrics_middleware(
    app,
    metrics=initialize_metrics(),
    middleware_factory=MetricsMiddleware,
    logger=logger,
)

# SecurityMiddleware — input validation and security headers (before CORS)
# Probe endpoints stay unauthenticated for platform health/readiness checks.
_security_config_l6 = SecurityConfig.from_env(
    skip_validation_paths=frozenset({"/health", "/ready", "/metrics"}),
    strict_mode=True,
)
add_security_middleware(app, config=_security_config_l6)

# GovernanceMiddleware — provides auth and tenant context
try:
    from value_fabric.shared.identity.api_key_stub import reject_api_key_unsupported
    from value_fabric.shared.identity.middleware import GovernanceMiddleware

    app.add_middleware(GovernanceMiddleware, api_key_resolver=reject_api_key_unsupported)
except ImportError:
    if os.getenv("ENVIRONMENT") in ("production", "staging"):
        raise RuntimeError(
            "GovernanceMiddleware is required in production/staging — "
            "shared.identity must be importable"
        )
    logging.getLogger(__name__).warning(
        "shared.identity not importable — GovernanceMiddleware skipped in dev."
    )

# Custom metrics endpoint using our PrometheusMetrics class
@app.get("/metrics", tags=["Monitoring"], include_in_schema=False)
async def metrics_endpoint(request: Request):
    """Prometheus-compatible metrics endpoint.

    Internal-only — access is gated by ``shared.observability.verify_metrics_access``
    so that scrape-token auth and private-network rules stay aligned across layers.
    """
    if not verify_metrics_access(request):
        raise HTTPException(status_code=403, detail="Metrics endpoint requires internal access")

    metrics = get_metrics()

    if not metrics:
        return Response(
            content="# Metrics collection is disabled",
            status_code=503,
            media_type="text/plain"
        )

    try:
        metrics_data = metrics.get_metrics()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(
            content=f"# Error: {e}",
            status_code=500,
            media_type="text/plain"
        )


# Pydantic models for API (defined in schemas.py to avoid circular imports)
# API Routes
import time

from value_fabric.shared.models.typed_dict import TypedDictModel

from .schemas import (
    ComparisonRequestPayload,
    ComparisonResponse,
    DatasetDetail,
    DatasetSummary,
    ValidationRequestPayload,
    ValidationResponse,
)


class health_checkResult(TypedDictModel):
    datasets_loaded: Any
    dependencies: Any
    readiness: dict[str, Any]
    response_time_ms: Any
    service: str
    status: Any
    system: dict[str, Any]
    timestamp: Any
    version: str

class list_industriesResult(TypedDictModel):
    industries: Any


def _require_tenant_id(ctx: RequestContext | None) -> str:
    """Fail closed when a benchmark handler is invoked without tenant context."""
    if ctx is None or not getattr(ctx, "tenant_id", None):
        raise HTTPException(status_code=401, detail="Tenant context required")
    return str(ctx.tenant_id)


async def health_check(request: Request):
    """Health check endpoint with dependency and system status."""
    import psutil  # type: ignore[import-untyped]

    start_time = time.time()

    # Neo4j connectivity check. Avoid opening a fresh blocking Bolt retry loop
    # on lightweight health requests after startup already established that the
    # benchmark store is unavailable.
    if _benchmark_repo is None and _neo4j_startup_error:
        neo4j_status = {"status": "unavailable", "error": _neo4j_startup_error}
    else:
        neo4j_status = await neo4j_health_check()
    neo4j_healthy = neo4j_status.get("status") == "healthy"

    dataset_count = 0
    if _benchmark_repo is not None:
        try:
            datasets = await _benchmark_repo.list_datasets(tenant_id="system")
            dataset_count = len(datasets)
        except Exception as exc:
            logger.warning("Health check: failed to list datasets: %s", exc)

    # System metrics
    memory_info = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=None)

    dependencies = [
        {
            "name": "neo4j",
            "status": "healthy" if neo4j_healthy else "degraded",
            "response_time_ms": 0,
            "error": None if neo4j_healthy else neo4j_status.get("error"),
        },
        {
            "name": "benchmark_dataset_store",
            "status": "healthy" if dataset_count > 0 else "degraded",
            "response_time_ms": 0,
            "error": None if dataset_count > 0 else "No benchmark datasets are loaded",
        },
    ]

    overall_status = "healthy" if all(d["status"] == "healthy" for d in dependencies) else "degraded"
    response_time_ms = round((time.time() - start_time) * 1000, 2)

    # Update Prometheus health metrics if available
    if request and hasattr(request.app.state, "metrics") and request.app.state.metrics:
        request.app.state.metrics.set_health_status(overall_status == "healthy", component="api")
        request.app.state.metrics.set_datasets_loaded(dataset_count)

    return health_checkResult.model_validate(build_health_response(
        service_name="layer6-benchmarks",
        status=overall_status,
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        response_time_ms=response_time_ms,
        datasets_loaded=dataset_count,
        dependencies=dependencies,
        readiness={
            "is_ready": overall_status in {"healthy", "degraded"},
            "reason": "dependencies_available" if overall_status in {"healthy", "degraded"} else "dependencies_unavailable",
        },
        system={
            "memory_usage_mb": round(memory_info.used / (1024 * 1024), 2),
            "memory_percent": memory_info.percent,
            "cpu_percent": cpu_percent,
        },
    ))


async def list_datasets(
    industry: Optional[str] = None,
    segment: Optional[str] = None,
    ctx: RequestContext = Depends(get_request_context),
):
    """List available benchmark datasets."""
    if _benchmark_repo is None:
        raise HTTPException(status_code=503, detail="Benchmark store not initialized")
    tenant_id = _require_tenant_id(ctx)
    datasets = await _benchmark_repo.list_datasets(industry=industry, segment=segment, tenant_id=tenant_id)
    return [
        DatasetSummary(
            dataset_id=d.dataset_id,
            name=d.name,
            description=d.description,
            industry=d.industry,
            segment=d.segment,
            geography=d.geography,
            metrics=list(d.metrics.keys()),
            metric_count=len(d.metrics),
            version=d.version,
            data_source=d.data_source,
        )
        for d in datasets
    ]


async def get_dataset(dataset_id: str, ctx: RequestContext = Depends(get_request_context)):
    """Get benchmark dataset by ID."""
    if _benchmark_repo is None:
        raise HTTPException(status_code=503, detail="Benchmark store not initialized")
    tenant_id = _require_tenant_id(ctx)
    dataset = await _benchmark_repo.get_dataset(dataset_id, tenant_id=tenant_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return DatasetDetail(
        dataset_id=dataset.dataset_id,
        name=dataset.name,
        description=dataset.description,
        industry=dataset.industry,
        segment=dataset.segment,
        geography=dataset.geography,
        metrics={
            name: {
                "name": m.name,
                "unit": m.unit,
                "description": m.description,
                "profile": m.profile.to_dict(),
            }
            for name, m in dataset.metrics.items()
        },
        version=dataset.version,
        data_source=dataset.data_source,
    )


async def compare(payload: ComparisonRequestPayload, ctx: RequestContext = Depends(get_request_context)):
    """Execute peer comparison."""
    if _benchmark_repo is None:
        raise HTTPException(status_code=503, detail="Benchmark store not initialized")
    tenant_id = _require_tenant_id(ctx)
    dataset = await _benchmark_repo.get_dataset(payload.dataset_id, tenant_id=tenant_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    metric = dataset.get_metric(payload.metric)
    if not metric:
        raise HTTPException(status_code=404, detail=f"Metric '{payload.metric}' not found")

    try:
        company_value = Decimal(payload.company_value)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid company_value format")

    profile = metric.profile

    # Calculate percentile (simplified)
    if company_value <= profile.p10:
        percentile = 5
    elif company_value <= profile.p25:
        percentile = 17
    elif company_value <= profile.p50:
        percentile = 37
    elif company_value <= profile.p75:
        percentile = 62
    elif company_value <= profile.p90:
        percentile = 82
    else:
        percentile = 95

    # Assessment
    if percentile >= 80:
        assessment = "top performer"
    elif percentile >= 60:
        assessment = "above average"
    elif percentile >= 40:
        assessment = "average"
    elif percentile >= 20:
        assessment = "below average"
    else:
        assessment = "needs improvement"

    # Confidence based on sample size
    if profile.sample_size >= 1000:
        confidence = "high"
    elif profile.sample_size >= 500:
        confidence = "medium"
    else:
        confidence = "low"

    return ComparisonResponse(
        percentile=percentile,
        peer_median=str(profile.p50),
        peer_range=(str(profile.p10), str(profile.p90)),
        sample_size=profile.sample_size,
        confidence=confidence,
        assessment=assessment,
    )


async def validate(payload: ValidationRequestPayload, ctx: RequestContext = Depends(get_request_context)):
    """Validate value against benchmark range."""
    if _benchmark_repo is None:
        raise HTTPException(status_code=503, detail="Benchmark store not initialized")
    tenant_id = _require_tenant_id(ctx)
    dataset = await _benchmark_repo.get_dataset(payload.dataset_id, tenant_id=tenant_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    metric = dataset.get_metric(payload.metric)
    if not metric:
        raise HTTPException(status_code=404, detail=f"Metric '{payload.metric}' not found")

    try:
        value = Decimal(payload.value)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid value format")

    profile = metric.profile

    # Calculate expected range with tolerance
    tolerance_factor = Decimal(payload.tolerance_percent) / Decimal(100)
    range_min = profile.p10 * (Decimal(1) - tolerance_factor)
    range_max = profile.p90 * (Decimal(1) + tolerance_factor)

    # Check if within range
    is_valid = range_min <= value <= range_max

    # Calculate deviation
    median = profile.p50
    if value != median:
        deviation_percent = float((value - median) / median * 100)
    else:
        deviation_percent = 0.0

    # Determine severity
    if is_valid:
        severity = "info"
        message = f"Value {value} is within expected range ({range_min} - {range_max})"
    else:
        abs_deviation = abs(deviation_percent)
        if abs_deviation > 50:
            severity = "error"
            message = f"Value {value} significantly deviates from benchmark median ({median})"
        elif abs_deviation > 25:
            severity = "warning"
            message = f"Value {value} moderately deviates from benchmark median ({median})"
        else:
            severity = "info"
            message = f"Value {value} slightly outside tolerance range"

    return ValidationResponse(
        is_valid=is_valid,
        expected_range=(str(range_min), str(range_max)),
        actual_value=str(value),
        deviation_percent=deviation_percent,
        severity=severity,
        message=message,
    )


async def list_industries(ctx: RequestContext = Depends(get_request_context)):
    """List available industries."""
    if _benchmark_repo is None:
        raise HTTPException(status_code=503, detail="Benchmark store not initialized")
    tenant_id = _require_tenant_id(ctx)
    datasets = await _benchmark_repo.list_datasets(tenant_id=tenant_id)
    industries = {d.industry for d in datasets}
    return list_industriesResult.model_validate({"industries": sorted(industries)})


register_health_endpoint(app, service_name="layer6-benchmarks", handler=health_check)

app.include_router(system.router)
app.include_router(benchmarks.router)

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8006"))
    uvicorn.run(app, host="0.0.0.0", port=port)
