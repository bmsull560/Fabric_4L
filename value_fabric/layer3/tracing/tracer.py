"""Request tracing and distributed context propagation system."""

import contextvars
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from ..logging_config import get_logger

logger = get_logger(__name__)


class SpanKind(str, Enum):
    """Span types."""

    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"
    INTERNAL = "internal"


class SpanStatus(str, Enum):
    """Span status codes."""

    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class TraceContext:
    """Distributed trace context."""

    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    baggage: dict[str, str] = field(default_factory=dict)
    sampled: bool = True
    flags: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, str]:
        """Convert trace context to dictionary for propagation."""
        result = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "sampled": str(self.sampled).lower(),
        }

        if self.parent_span_id:
            result["parent_span_id"] = self.parent_span_id

        # Add baggage items
        for key, value in self.baggage.items():
            result[f"baggage_{key}"] = value

        # Add flags
        for key, value in self.flags.items():
            result[f"flag_{key}"] = str(value)

        return result

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "TraceContext":
        """Create trace context from dictionary."""
        baggage = {}
        flags = {}

        # Extract baggage items
        for key, value in data.items():
            if key.startswith("baggage_"):
                baggage[key[8:]] = value  # Remove "baggage_" prefix
            elif key.startswith("flag_"):
                flags[key[5:]] = value  # Remove "flag_" prefix

        return cls(
            trace_id=data.get("trace_id", ""),
            span_id=data.get("span_id", ""),
            parent_span_id=data.get("parent_span_id"),
            baggage=baggage,
            sampled=data.get("sampled", "true").lower() == "true",
            flags=flags,
        )


@dataclass
class SpanEvent:
    """Span event for recording significant moments."""

    timestamp: datetime
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return SpanEvent_to_dictResult.model_validate({
            "timestamp": self.timestamp.isoformat(),
            "name": self.name,
            "attributes": self.attributes,
        })


@dataclass
class SpanLink:
    """Link to another span."""

    trace_id: str
    span_id: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert link to dictionary."""
        return SpanLink_to_dictResult.model_validate({
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "attributes": self.attributes,
        })


class Span:
    """Distributed tracing span."""

    def __init__(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        trace_context: TraceContext | None = None,
        start_time: datetime | None = None,
        attributes: dict[str, Any] | None = None,
    ):
        """Initialize span.

        Args:
            name: Span name
            kind: Span kind
            trace_context: Trace context
            start_time: Start time
            attributes: Initial attributes
        """
        self.name = name
        self.kind = kind
        self.start_time = start_time or datetime.now(UTC)
        self.end_time: datetime | None = None
        self.status = SpanStatus.OK
        self.status_message: str | None = None

        # Set up trace context
        if trace_context:
            self.trace_context = trace_context
        else:
            self.trace_context = TraceContext(
                trace_id=str(uuid.uuid4()), span_id=str(uuid.uuid4())[:16], sampled=True
            )

        self.attributes = attributes or {}
        self.events: list[SpanEvent] = []
        self.links: list[SpanLink] = []
        self.resource: dict[str, Any] = {}
        self.library: dict[str, Any] = {}

        # Add basic attributes
        self._add_basic_attributes()

    def _add_basic_attributes(self):
        """Add basic span attributes."""
        self.attributes.update(
            {
                "span.kind": self.kind.value,
                "span.name": self.name,
                "service.name": "value-fabric-layer3",
                "service.version": "1.0.0",
                "process.pid": os.getpid() if "os" in globals() else None,
                "thread.id": threading.current_thread().ident
                if "threading" in globals()
                else None,
            }
        )

    def set_attribute(self, key: str, value: Any) -> None:
        """Set span attribute.

        Args:
            key: Attribute key
            value: Attribute value
        """
        self.attributes[key] = value

    def set_attributes(self, attributes: dict[str, Any]) -> None:
        """Set multiple span attributes.

        Args:
            attributes: Attributes to set
        """
        self.attributes.update(attributes)

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add event to span.

        Args:
            name: Event name
            attributes: Event attributes
        """
        event = SpanEvent(
            timestamp=datetime.now(UTC), name=name, attributes=attributes or {}
        )
        self.events.append(event)

    def add_link(
        self, trace_id: str, span_id: str, attributes: dict[str, Any] | None = None
    ) -> None:
        """Add link to another span.

        Args:
            trace_id: Linked trace ID
            span_id: Linked span ID
            attributes: Link attributes
        """
        link = SpanLink(trace_id=trace_id, span_id=span_id, attributes=attributes or {})
        self.links.append(link)

    def set_status(self, status: SpanStatus, message: str | None = None) -> None:
        """Set span status.

        Args:
            status: Span status
            message: Status message
        """
        self.status = status
        self.status_message = message

    def set_error(self, error: Exception) -> None:
        """Set span as error with exception details.

        Args:
            error: Exception that occurred
        """
        self.set_status(SpanStatus.ERROR, str(error))
        self.set_attributes(
            {
                "error.type": type(error).__name__,
                "error.message": str(error),
                "error.stack_trace": traceback.format_exc()
                if "traceback" in globals()
                else None,
            }
        )

        # Add error event
        self.add_event(
            name="exception",
            attributes={
                "exception.type": type(error).__name__,
                "exception.message": str(error),
                "exception.stack_trace": traceback.format_exc()
                if "traceback" in globals()
                else None,
            },
        )

    def end(self, end_time: datetime | None = None) -> None:
        """End the span.

        Args:
            end_time: End time (defaults to now)
        """
        self.end_time = end_time or datetime.now(UTC)

        # Calculate duration
        if self.start_time:
            duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
            self.attributes["span.duration_ms"] = duration_ms

    def to_dict(self) -> dict[str, Any]:
        """Convert span to dictionary for export.

        Returns:
            Span dictionary
        """
        result = {
            "trace_id": self.trace_context.trace_id,
            "span_id": self.trace_context.span_id,
            "parent_span_id": self.trace_context.parent_span_id,
            "name": self.name,
            "kind": self.kind.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status.value,
            "status_message": self.status_message,
            "attributes": self.attributes,
            "events": [event.to_dict() for event in self.events],
            "links": [link.to_dict() for link in self.links],
            "resource": self.resource,
            "library": self.library,
            "sampled": self.trace_context.sampled,
        }

        return result


class Tracer:
    """Distributed tracer."""

    def __init__(self, service_name: str = "value-fabric-layer3"):
        """Initialize tracer.

        Args:
            service_name: Service name for traces
        """
        self.service_name = service_name
        self.active_spans: dict[str, Span] = {}
        self.finished_spans: list[Span] = []
        self.max_finished_spans = 1000  # Limit memory usage

        # Context variables for thread-local storage
        self.current_span = contextvars.ContextVar("current_span", default=None)
        self.current_trace_context = contextvars.ContextVar(
            "current_trace_context", default=None
        )

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent_context: TraceContext | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """Start a new span.

        Args:
            name: Span name
            kind: Span kind
            parent_context: Parent trace context
            attributes: Initial attributes

        Returns:
            Started span
        """
        # Create trace context for new span
        if parent_context:
            trace_context = TraceContext(
                trace_id=parent_context.trace_id,
                span_id=str(uuid.uuid4())[:16],
                parent_span_id=parent_context.span_id,
                baggage=parent_context.baggage.copy(),
                sampled=parent_context.sampled,
                flags=parent_context.flags.copy(),
            )
        else:
            # Get current context if available
            current_context = self.current_trace_context.get()
            if current_context:
                trace_context = TraceContext(
                    trace_id=current_context.trace_id,
                    span_id=str(uuid.uuid4())[:16],
                    parent_span_id=current_context.span_id,
                    baggage=current_context.baggage.copy(),
                    sampled=current_context.sampled,
                    flags=current_context.flags.copy(),
                )
            else:
                trace_context = TraceContext(
                    trace_id=str(uuid.uuid4()),
                    span_id=str(uuid.uuid4())[:16],
                    sampled=True,
                )

        # Create span
        span = Span(
            name=name, kind=kind, trace_context=trace_context, attributes=attributes
        )

        # Store active span
        self.active_spans[span.trace_context.span_id] = span

        # Set current context
        self.current_span.set(span)
        self.current_trace_context.set(trace_context)

        logger.debug(f"Started span: {name} ({span.trace_context.span_id})")

        return span

    def end_span(self, span: Span) -> None:
        """End a span.

        Args:
            span: Span to end
        """
        span.end()

        # Move from active to finished
        if span.trace_context.span_id in self.active_spans:
            del self.active_spans[span.trace_context.span_id]

        self.finished_spans.append(span)

        # Limit finished spans to prevent memory leaks
        if len(self.finished_spans) > self.max_finished_spans:
            self.finished_spans = self.finished_spans[-self.max_finished_spans :]

        # Clear current context if this was the current span
        current = self.current_span.get()
        if current and current.trace_context.span_id == span.trace_context.span_id:
            self.current_span.set(None)

        logger.debug(f"Ended span: {span.name} ({span.trace_context.span_id})")

    def get_current_span(self) -> Span | None:
        """Get current active span.

        Returns:
            Current span or None
        """
        return self.current_span.get()

    def get_current_trace_context(self) -> TraceContext | None:
        """Get current trace context.

        Returns:
            Current trace context or None
        """
        return self.current_trace_context.get()

    def create_trace_context_headers(self) -> dict[str, str]:
        """Create HTTP headers for trace context propagation.

        Returns:
            Headers dictionary
        """
        context = self.get_current_trace_context()
        if not context:
            return Tracer_create_trace_context_headersResult.model_validate({})

        return Tracer_create_trace_context_headersResult.model_validate({
            "X-Trace-Id": context.trace_id,
            "X-Span-Id": context.span_id,
            "X-Parent-Span-Id": context.parent_span_id or "",
            "X-Trace-Sampled": str(context.sampled).lower(),
        })


    def extract_trace_context_from_headers(
        self, headers: dict[str, str]
    ) -> TraceContext | None:
        """Extract trace context from HTTP headers.

        Args:
            headers: HTTP headers

        Returns:
            Trace context or None
        """
        trace_id = (
            headers.get("X-Trace-Id") or headers.get("traceparent", "").split("-")[0]
        )
        span_id = headers.get("X-Span-Id")
        parent_span_id = headers.get("X-Parent-Span-Id")
        sampled = headers.get("X-Trace-Sampled", "true").lower() == "true"

        if not trace_id or not span_id:
            return None

        # Extract baggage items
        baggage = {}
        for key, value in headers.items():
            if key.startswith("X-Baggage-"):
                baggage[key[10:]] = value  # Remove "X-Baggage-" prefix

        return TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id if parent_span_id else None,
            baggage=baggage,
            sampled=sampled,
        )

    def get_trace_summary(self) -> dict[str, Any]:
        """Get trace summary statistics.

        Returns:
            Trace summary
        """
        total_spans = len(self.active_spans) + len(self.finished_spans)

        # Status distribution
        status_counts = defaultdict(int)
        for span in self.active_spans.values():
            status_counts[span.status.value] += 1
        for span in self.finished_spans:
            status_counts[span.status.value] += 1

        # Kind distribution
        kind_counts = defaultdict(int)
        for span in self.active_spans.values():
            kind_counts[span.kind.value] += 1
        for span in self.finished_spans:
            kind_counts[span.kind.value] += 1

        # Average duration
        durations = []
        for span in self.finished_spans:
            if span.end_time and span.start_time:
                duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
                durations.append(duration_ms)

        avg_duration_ms = sum(durations) / len(durations) if durations else 0

        return Tracer_get_trace_summaryResult.model_validate({
            "service_name": self.service_name,
            "active_spans": len(self.active_spans),
            "finished_spans": len(self.finished_spans),
            "total_spans": total_spans,
            "status_distribution": dict(status_counts),
            "kind_distribution": dict(kind_counts),
            "average_duration_ms": avg_duration_ms,
            "max_finished_spans": self.max_finished_spans,
        })


    def export_spans(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Export finished spans.

        Args:
            limit: Maximum number of spans to export

        Returns:
            List of span dictionaries
        """
        spans = self.finished_spans
        if limit:
            spans = spans[-limit:]

        return [span.to_dict() for span in spans]


# Context manager for automatic span management
class SpanContext:
    """Context manager for automatic span lifecycle management."""

    def __init__(
        self,
        tracer: Tracer,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] | None = None,
    ):
        """Initialize span context.

        Args:
            tracer: Tracer instance
            name: Span name
            kind: Span kind
            attributes: Initial attributes
        """
        self.tracer = tracer
        self.name = name
        self.kind = kind
        self.attributes = attributes
        self.span: Span | None = None

    def __enter__(self) -> Span:
        """Enter context and start span."""
        self.span = self.tracer.start_span(
            name=self.name, kind=self.kind, attributes=self.attributes
        )
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and end span."""
        if self.span:
            if exc_type and exc_val:
                self.span.set_error(exc_val)
            self.tracer.end_span(self.span)


# Decorator for automatic function tracing
def trace_function(
    name: str | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
):
    """Decorator to automatically trace functions.

    Args:
        name: Span name (defaults to function name)
        kind: Span kind
        attributes: Initial attributes

    Returns:
        Decorated function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or f"{func.__module__}.{func.__name__}"

            with SpanContext(tracer, span_name, kind, attributes):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Global tracer instance
_tracer: Tracer | None = None


def get_tracer() -> Tracer:
    """Get global tracer instance.

    Returns:
        Tracer instance
    """
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def initialize_tracing(service_name: str = "value-fabric-layer3") -> Tracer:
    """Initialize global tracing system.

    Args:
        service_name: Service name for traces

    Returns:
        Tracer instance
    """
    global _tracer
    _tracer = Tracer(service_name)
    logger.info(f"Tracing initialized for service: {service_name}")
    return _tracer


# Convenience functions
def start_span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
) -> Span:
    """Start a new span with the global tracer.

    Args:
        name: Span name
        kind: Span kind
        attributes: Initial attributes

    Returns:
        Started span
    """
    tracer = get_tracer()
    return tracer.start_span(name, kind, attributes)


def get_current_span() -> Span | None:
    """Get current active span.

    Returns:
        Current span or None
    """
    tracer = get_tracer()
    return tracer.get_current_span()


def get_current_trace_context() -> TraceContext | None:
    """Get current active trace context."""
    tracer = get_tracer()
    return tracer.get_current_trace_context()


def get_trace_headers() -> dict[str, str]:
    """Get trace context headers for propagation.

    Returns:
        Headers dictionary
    """
    tracer = get_tracer()
    return tracer.create_trace_context_headers()


def set_baggage_item(key: str, value: str) -> None:
    """Set baggage item in current trace context.

    Args:
        key: Baggage key
        value: Baggage value
    """
    context = get_current_trace_context()
    if context:
        context.baggage[key] = value


def get_baggage_item(key: str) -> str | None:
    """Get baggage item from current trace context.

    Args:
        key: Baggage key

    Returns:
        Baggage value or None
    """
    context = get_current_trace_context()
    if context:
        return context.baggage.get(key)
    return None


# Import required modules for basic attributes
import os
import threading
import traceback

from value_fabric.shared.models.typed_dict import TypedDictModel


class SpanEvent_to_dictResult(TypedDictModel):
    attributes: Any
    name: Any
    timestamp: Any

class SpanLink_to_dictResult(TypedDictModel):
    attributes: Any
    span_id: Any
    trace_id: Any

class Tracer_create_trace_context_headersResult(TypedDictModel):
    x_parent_span_id: bool | None = None
    x_span_id: Any | None = None
    x_trace_id: Any | None = None
    x_trace_sampled: Any | None = None

class Tracer_get_trace_summaryResult(TypedDictModel):
    active_spans: Any
    average_duration_ms: Any
    finished_spans: Any
    kind_distribution: dict[str, Any]
    max_finished_spans: Any
    service_name: Any
    status_distribution: dict[str, Any]
    total_spans: Any
