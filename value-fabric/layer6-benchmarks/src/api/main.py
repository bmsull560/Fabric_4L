"""Layer 6 Benchmark Service - FastAPI main application.

Standalone service on port 8006 for comparative intelligence.
P1-29: OpenTelemetry tracing integration for observability.
"""

import logging
import os
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Any, Dict, Optional

# Logger defined early so lifespan() and module-level instrumentation can use it.
logger = logging.getLogger(__name__)

try:
    from shared.secrets import load_infisical_secrets
    load_infisical_secrets()
except ImportError:
    pass  # shared package not available; env vars used directly

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

# P1-29: OpenTelemetry imports for distributed tracing
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

try:
    from shared.security import SecurityConfig, add_security_middleware
except ImportError:
    add_security_middleware = None
    SecurityConfig = None

try:
    from shared.observability import verify_metrics_access
except ImportError:  # pragma: no cover
    verify_metrics_access = None  # type: ignore[assignment]

from ..metrics import MetricsMiddleware, get_metrics, initialize_metrics
from ..models.benchmark_dataset import (
    MANUFACTURING_BENCHMARK_SEED,
    BenchmarkDataset,
    BenchmarkMetric,
    StatisticalProfile,
)
from .routes import benchmarks, system

# In-memory storage (replace with Neo4j in production)
_benchmark_store: Dict[str, BenchmarkDataset] = {}

# P1-29: OpenTelemetry tracer provider (initialized on startup)
_tracer_provider: TracerProvider | None = None


def init_telemetry() -> TracerProvider | None:
    """Initialize OpenTelemetry tracing if endpoint configured.

    P1-29: OpenTelemetry integration for distributed tracing.
    """
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otel_endpoint:
        return None

    resource = Resource.create({SERVICE_NAME: "layer6-benchmarks"})
    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=f"{otel_endpoint}/v1/traces"
    )
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    return provider


def _init_seed_data():
    """Initialize with manufacturing benchmark dataset."""
    seed = MANUFACTURING_BENCHMARK_SEED
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

    _benchmark_store[dataset.dataset_id] = dataset


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _tracer_provider

    # P1-29: Initialize OpenTelemetry
    _tracer_provider = init_telemetry()
    if _tracer_provider:
        logger.info("L6: OpenTelemetry tracing initialized")

    # Initialize Prometheus metrics
    metrics = initialize_metrics()
    if metrics:
        logger.info("Prometheus metrics initialized")
    app.state.metrics = metrics

    # Add metrics middleware if available
    if metrics:
        metrics_middleware = MetricsMiddleware(metrics)
        app.middleware("http")(metrics_middleware)
        logger.info("L6: Metrics middleware installed")

    # Startup
    _init_seed_data()
    dataset_count = len(_benchmark_store)
    if metrics:
        metrics.set_datasets_loaded(dataset_count)
    logger.info(f"Layer 6 Benchmark Service started with {dataset_count} datasets")
    yield
    # Shutdown
    _benchmark_store.clear()


app = FastAPI(
    title="Value Fabric - Benchmark Service",
    description="Comparative intelligence and peer benchmarking API",
    version="1.0.0",
    lifespan=lifespan,
)

# P1-29: Instrument FastAPI with OpenTelemetry (after app creation)
if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
    FastAPIInstrumentor.instrument_app(app)
    logger.info("L6: FastAPI instrumented with OpenTelemetry")

# SecurityMiddleware — input validation and security headers (before CORS)
# L6 has no skip paths — all endpoints require strict validation
if SecurityConfig and add_security_middleware:
    _security_config_l6 = SecurityConfig.from_env(
        skip_validation_paths=frozenset(),
        strict_mode=True,
    )
    add_security_middleware(app, config=_security_config_l6)

# GovernanceMiddleware — provides auth and tenant context
try:
    from shared.identity.api_key_stub import reject_api_key_unsupported
    from shared.identity.middleware import GovernanceMiddleware

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

# CORS middleware with production validation (P0-20)
# Note: allow_origins=["*"] cannot be used with allow_credentials=True per browser security spec
_environment = os.getenv("ENVIRONMENT", "development")
_cors_origins_env = os.getenv("CORS_ORIGINS", "")

if _environment == "production" and not _cors_origins_env:
    raise RuntimeError(
        "FATAL: CORS_ORIGINS environment variable must be set in production. "
        "Use 'https://yourdomain.com' or comma-separated list of allowed origins."
    )

# Parse CORS origins, filtering out empty strings from trailing commas
allow_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()] if _cors_origins_env else ["*"]
# Credentials can only be allowed with specific origins, never with wildcard (browser security requirement)
allow_credentials = "*" not in allow_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom metrics endpoint using our PrometheusMetrics class
@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint(request: Request):
    """Prometheus-compatible metrics endpoint.

    Internal-only — access is gated by ``shared.observability.verify_metrics_access``
    so that scrape-token auth and private-network rules stay aligned across layers.
    """
    if verify_metrics_access is None or not verify_metrics_access(request):
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
from datetime import datetime

from shared.models.typed_dict import TypedDictModel

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
    response_time_ms: Any
    service: str
    status: Any
    system: dict[str, Any]
    timestamp: Any
    version: str

class list_industriesResult(TypedDictModel):
    industries: Any


async def health_check(request: Request = None):
    """Health check endpoint with dependency and system status."""
    import psutil

    start_time = time.time()

    dataset_count = len(_benchmark_store)

    # System metrics
    memory_info = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=None)

    # Layer 6 uses benchmark dataset store as a runtime dependency.
    dependencies = [
        {
            "name": "benchmark_dataset_store",
            "status": "healthy" if dataset_count > 0 else "degraded",
            "response_time_ms": 0,
            "error": None if dataset_count > 0 else "No benchmark datasets are loaded",
        }
    ]

    overall_status = "healthy" if all(d["status"] == "healthy" for d in dependencies) else "degraded"
    response_time_ms = round((time.time() - start_time) * 1000, 2)

    # Update Prometheus health metrics if available
    if request and hasattr(request.app.state, "metrics") and request.app.state.metrics:
        request.app.state.metrics.set_health_status(overall_status == "healthy", component="api")
        request.app.state.metrics.set_datasets_loaded(dataset_count)

    return health_checkResult.model_validate({
        "status": overall_status,
        "service": "layer6-benchmarks",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "response_time_ms": response_time_ms,
        "datasets_loaded": dataset_count,
        "dependencies": dependencies,
        "system": {
            "memory_usage_mb": round(memory_info.used / (1024 * 1024), 2),
            "memory_percent": memory_info.percent,
            "cpu_percent": cpu_percent,
        },
    })


async def list_datasets(
    industry: Optional[str] = None,
    segment: Optional[str] = None,
):
    """List available benchmark datasets."""
    datasets = []
    for dataset in _benchmark_store.values():
        if industry and dataset.industry != industry:
            continue
        if segment and dataset.segment != segment:
            continue
        datasets.append(
            DatasetSummary(
                dataset_id=dataset.dataset_id,
                name=dataset.name,
                industry=dataset.industry,
                segment=dataset.segment,
                metrics=list(dataset.metrics.keys()),
                version=dataset.version,
            )
        )
    return datasets


async def get_dataset(dataset_id: str):
    """Get benchmark dataset by ID."""
    dataset = _benchmark_store.get(dataset_id)
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


async def compare(payload: ComparisonRequestPayload):
    """Execute peer comparison."""
    dataset = _benchmark_store.get(payload.dataset_id)
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


async def validate(payload: ValidationRequestPayload):
    """Validate value against benchmark range."""
    dataset = _benchmark_store.get(payload.dataset_id)
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


async def list_industries():
    """List available industries."""
    industries = set()
    for dataset in _benchmark_store.values():
        industries.add(dataset.industry)
    return list_industriesResult.model_validate({"industries": sorted(industries)})

app.include_router(system.router)
app.include_router(benchmarks.router)

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8006"))
    uvicorn.run(app, host="0.0.0.0", port=port)
