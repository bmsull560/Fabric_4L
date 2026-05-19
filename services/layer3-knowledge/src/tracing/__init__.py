"""Tracing package initialization."""

from ..tracing.middleware import (
    BusinessLogicTracer,
    CacheTracer,
    DatabaseTracer,
    ExternalServiceTracer,
    StreamingResponseTracer,
    TracingMiddleware,
    add_span_attributes,
    add_span_event,
    get_current_span_dependency,
    get_trace_context_dependency,
    get_trace_id_dependency,
)
from ..tracing.tracer import (
    Span,
    SpanContext,
    SpanEvent,
    SpanKind,
    SpanLink,
    SpanStatus,
    TraceContext,
    Tracer,
    get_baggage_item,
    get_current_span,
    get_trace_headers,
    get_tracer,
    initialize_tracing,
    set_baggage_item,
    start_span,
    trace_function,
)

__all__ = [
    # Core tracing
    "TraceContext",
    "Span",
    "SpanKind",
    "SpanStatus",
    "SpanEvent",
    "SpanLink",
    "Tracer",
    "SpanContext",
    # Utilities
    "trace_function",
    "get_tracer",
    "initialize_tracing",
    "start_span",
    "get_current_span",
    "get_trace_headers",
    "set_baggage_item",
    "get_baggage_item",
    # Middleware
    "TracingMiddleware",
    "StreamingResponseTracer",
    "add_span_attributes",
    "add_span_event",
    # Specialized tracers
    "DatabaseTracer",
    "CacheTracer",
    "ExternalServiceTracer",
    "BusinessLogicTracer",
    # FastAPI dependencies
    "get_current_span_dependency",
    "get_trace_context_dependency",
    "get_trace_id_dependency",
]
