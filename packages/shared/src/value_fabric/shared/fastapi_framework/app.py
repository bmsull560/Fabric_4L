"""Reusable FastAPI application assembly helpers."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI

from ..error_handling.handlers import register_exception_handlers

from .middleware import CorsPolicy, add_cors_middleware, add_request_id_middleware


def init_telemetry(service_name: str, *, endpoint: str | None = None) -> Any | None:
    import os

    otel_endpoint = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otel_endpoint:
        return None

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        return None

    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=f"{otel_endpoint}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return provider


def instrument_fastapi_app(app: FastAPI, *, enabled: bool) -> None:
    if not enabled:
        return

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ImportError:
        return

    FastAPIInstrumentor.instrument_app(app)


def build_health_response(
    *,
    service_name: str,
    status: str = "ok",
    version: str | None = None,
    timestamp: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "status": status,
        "service": service_name,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }
    if version is not None:
        response["version"] = version
    response.update(extra)
    return response


def register_health_endpoint(
    app: FastAPI,
    *,
    service_name: str,
    path: str = "/health",
    include_in_schema: bool = True,
    handler: Callable[..., Any] | None = None,
) -> None:
    if handler is None:
        async def default_handler() -> dict[str, Any]:
            return build_health_response(service_name=service_name)

        route_handler = default_handler
    else:
        route_handler = handler

    app.add_api_route(
        path,
        route_handler,
        methods=["GET"],
        include_in_schema=include_in_schema,
        tags=["health"],
    )


def install_metrics_middleware(
    app: FastAPI,
    *,
    metrics: Any | None,
    middleware_factory: Callable[[Any], Any],
    logger: Any | None = None,
) -> Any | None:
    """Attach a service metrics instance and install its HTTP middleware once."""

    if metrics is None:
        return None

    app.state.metrics = metrics
    if getattr(app.state, "_metrics_middleware_installed", False):
        return metrics

    app.middleware("http")(middleware_factory(metrics))
    app.state._metrics_middleware_installed = True
    if logger is not None:
        logger.info("Metrics middleware installed")

    return metrics


def create_fabric_app(
    *,
    service_name: str,
    title: str,
    version: str,
    description: str,
    lifespan: Callable[..., Any] | None = None,
    cors_policy: CorsPolicy | dict[str, Any] | None = None,
    register_default_exception_handlers: bool = True,
    include_request_id_middleware: bool = True,
    telemetry_service_name: str | None = None,
    instrument_telemetry: bool = False,
) -> FastAPI:
    """Create a FastAPI application with Value Fabric defaults.

    This factory centralizes the common bootstrap concerns that are repeated
    across service entrypoints without constraining service-specific startup
    dependencies or router composition.
    """

    app = FastAPI(
        title=title,
        version=version,
        description=description,
        lifespan=lifespan,
    )
    app.state.service_name = service_name
    app.state.telemetry_provider = None

    if telemetry_service_name is not None:
        app.state.telemetry_provider = init_telemetry(telemetry_service_name)
        if instrument_telemetry:
            instrument_fastapi_app(app, enabled=app.state.telemetry_provider is not None)

    if cors_policy is not None:
        policy = cors_policy if isinstance(cors_policy, CorsPolicy) else CorsPolicy(**cors_policy)
        add_cors_middleware(app, policy)

    if include_request_id_middleware:
        add_request_id_middleware(app)

    if register_default_exception_handlers:
        register_exception_handlers(app)

    return app