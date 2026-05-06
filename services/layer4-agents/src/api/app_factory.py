"""Layer 4 FastAPI application factory."""

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from value_fabric.shared.security import validate_production_safety

from ..config.settings import settings
from ..metrics import initialize_metrics
from .middleware import configure_middleware
from .routers import register_routers
from .startup import build_lifespan, start_optional_integrations


def init_telemetry() -> TracerProvider | None:
    if not settings.otel_exporter_endpoint:
        return None
    resource = Resource.create({SERVICE_NAME: "layer4-agents"})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=f"{settings.otel_exporter_endpoint}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return provider


def create_app() -> FastAPI:
    app = FastAPI(
        title="Layer 4: Agentic Workflow Engine",
        description="LangGraph-powered workflow orchestration for Value Fabric with multi-agent support",
        version="0.2.0",
        lifespan=build_lifespan(
            validate_production_safety=validate_production_safety,
            init_telemetry=init_telemetry,
            configure_optional_integrations=start_optional_integrations,
        ),
    )

    if settings.otel_exporter_endpoint:
        FastAPIInstrumentor.instrument_app(app)

    try:
        from value_fabric.shared.identity.dev_bypass import maybe_install_dev_bypass
        maybe_install_dev_bypass(app)
    except Exception:
        pass

    app.state.metrics = initialize_metrics()
    configure_middleware(app)
    register_routers(app)
    return app
