# OpenTelemetry conditional import fix for layer3
# This wrapper makes opentelemetry optional

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None
    OTLPSpanExporter = None
    FastAPIInstrumentor = None
    SERVICE_NAME = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None

__all__ = [
    "OTEL_AVAILABLE",
    "trace",
    "OTLPSpanExporter",
    "FastAPIInstrumentor",
    "SERVICE_NAME",
    "Resource",
    "TracerProvider",
    "BatchSpanProcessor",
]
