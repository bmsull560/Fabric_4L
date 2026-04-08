"""Tracing package initialization."""

from .tracer import (
    TraceContext,
    Span,
    SpanKind,
    SpanStatus,
    SpanEvent,
    SpanLink,
    Tracer,
    SpanContext,
    trace_function,
    get_tracer,
    initialize_tracing,
    start_span,
    get_current_span,
    get_trace_headers,
    set_baggage_item,
    get_baggage_item,
)

from .middleware import (
    TracingMiddleware,
    StreamingResponseTracer,
    add_span_attributes,
    add_span_event,
    DatabaseTracer,
    CacheTracer,
    ExternalServiceTracer,
    BusinessLogicTracer,
    get_current_span_dependency,
    get_trace_context_dependency,
    get_trace_id_dependency,
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
