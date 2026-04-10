"""FastAPI tracing middleware and integration."""

from typing import Callable, Dict, List, Optional, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from .tracer import (
    Tracer,
    Span,
    SpanKind,
    SpanStatus,
    get_tracer,
    initialize_tracing,
    SpanContext,
)
from ..logging_config import get_logger

logger = get_logger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware to add distributed tracing to FastAPI requests."""
    
    def __init__(self, app, tracer: Optional[Tracer] = None):
        """Initialize tracing middleware.
        
        Args:
            app: ASGI application
            tracer: Tracer instance
        """
        super().__init__(app)
        self.tracer = tracer or get_tracer()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracing."""
        # Extract trace context from headers
        trace_context = self.tracer.extract_trace_context_from_headers(dict(request.headers))
        
        # Start server span
        span = self.tracer.start_span(
            name=f"{request.method} {request.url.path}",
            kind=SpanKind.SERVER,
            parent_context=trace_context,
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.scheme": request.url.scheme,
                "http.host": request.url.hostname,
                "http.port": request.url.port,
                "http.path": request.url.path,
                "http.query": request.url.query,
                "http.user_agent": request.headers.get("User-Agent", ""),
                "http.remote_addr": request.client.host if request.client else "",
                "http.request_id": getattr(request.state, "request_id", None),
            }
        )
        
        # Store span in request state for access in endpoints
        request.state.span = span
        request.state.trace_context = span.trace_context
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record response attributes
            span.set_attributes({
                "http.status_code": response.status_code,
                "http.response_size": len(response.body) if hasattr(response, 'body') else 0,
            })
            
            # Set span status based on response
            if response.status_code >= 400:
                span.set_status(SpanStatus.ERROR, f"HTTP {response.status_code}")
            else:
                span.set_status(SpanStatus.OK)
            
            # Add trace headers to response
            self._add_trace_headers(response, span.trace_context)
            
            return response
            
        except Exception as exc:
            # Record exception
            span.set_error(exc)
            span.set_attributes({
                "error.type": type(exc).__name__,
                "error.message": str(exc),
            })
            
            # Re-raise the exception
            raise
            
        finally:
            # End the span
            self.tracer.end_span(span)
    
    def _add_trace_headers(self, response: Response, trace_context) -> None:
        """Add trace context headers to response.
        
        Args:
            response: HTTP response
            trace_context: Trace context
        """
        headers = response.headers
        headers["X-Trace-Id"] = trace_context.trace_id
        headers["X-Span-Id"] = trace_context.span_id
        
        if trace_context.parent_span_id:
            headers["X-Parent-Span-Id"] = trace_context.parent_span_id
        
        headers["X-Trace-Sampled"] = str(trace_context.sampled).lower()
        
        # Add baggage items
        for key, value in trace_context.baggage.items():
            headers[f"X-Baggage-{key}"] = value


class StreamingResponseTracer:
    """Helper for tracing streaming responses."""
    
    @staticmethod
    def trace_streaming_response(
        response: StreamingResponse,
        span: Span,
        total_size: Optional[int] = None
    ) -> StreamingResponse:
        """Wrap streaming response to add tracing.
        
        Args:
            response: Streaming response
            span: Current span
            total_size: Expected total size
            
        Returns:
            Traced streaming response
        """
        original_stream = response.body_iterator
        
        async def traced_stream():
            bytes_sent = 0
            try:
                async for chunk in original_stream():
                    bytes_sent += len(chunk)
                    yield chunk
            except Exception as exc:
                span.set_error(exc)
                raise
            finally:
                span.set_attributes({
                    "http.response_size": bytes_sent,
                    "http.stream_complete": True,
                })
                
                if total_size:
                    span.set_attributes({
                        "http.expected_size": total_size,
                        "http.size_ratio": bytes_sent / total_size if total_size > 0 else 0,
                    })
        
        response.body_iterator = traced_stream()
        return response


def add_span_attributes(attributes: Dict[str, Any]) -> Callable:
    """Decorator to add attributes to current span.
    
    Args:
        attributes: Attributes to add
        
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            span = get_current_span()
            if span:
                span.set_attributes(attributes)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> Callable:
    """Decorator to add event to current span.
    
    Args:
        name: Event name
        attributes: Event attributes
        
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            span = get_current_span()
            if span:
                span.add_event(name, attributes)
            return func(*args, **kwargs)
        return wrapper
    return decorator


class DatabaseTracer:
    """Helper for tracing database operations."""
    
    @staticmethod
    def trace_query(
        tracer: Tracer,
        query: str,
        database: str,
        operation: str = "query",
        parent_span: Optional[Span] = None
    ) -> SpanContext:
        """Trace a database query.
        
        Args:
            tracer: Tracer instance
            query: Database query
            database: Database name
            operation: Operation type
            parent_span: Parent span
            
        Returns:
            Span context
        """
        # Sanitize query for logging (remove sensitive data)
        sanitized_query = query[:200] + "..." if len(query) > 200 else query
        
        return SpanContext(
            tracer=tracer,
            name=f"{database}.{operation}",
            kind=SpanKind.CLIENT,
            attributes={
                "db.system": database,
                "db.operation": operation,
                "db.statement": sanitized_query,
                "db.query_type": operation.upper(),
            }
        )
    
    @staticmethod
    def trace_query_result(span: Span, result_count: int, duration_ms: float) -> None:
        """Record query result in span.
        
        Args:
            span: Query span
            result_count: Number of results
            duration_ms: Query duration in milliseconds
        """
        span.set_attributes({
            "db.rows_affected": result_count,
            "db.duration_ms": duration_ms,
            "db.success": True,
        })
    
    @staticmethod
    def trace_query_error(span: Span, error: Exception) -> None:
        """Record query error in span.
        
        Args:
            span: Query span
            error: Exception that occurred
        """
        span.set_error(error)
        span.set_attributes({
            "db.success": False,
            "db.error_type": type(error).__name__,
        })


class CacheTracer:
    """Helper for tracing cache operations."""
    
    @staticmethod
    def trace_cache_operation(
        tracer: Tracer,
        operation: str,
        cache_type: str,
        key: str,
        parent_span: Optional[Span] = None
    ) -> SpanContext:
        """Trace a cache operation.
        
        Args:
            tracer: Tracer instance
            operation: Operation type (get, set, delete)
            cache_type: Cache type (redis, memory)
            key: Cache key
            parent_span: Parent span
            
        Returns:
            Span context
        """
        return SpanContext(
            tracer=tracer,
            name=f"cache.{operation}",
            kind=SpanKind.CLIENT,
            attributes={
                "cache.system": cache_type,
                "cache.operation": operation,
                "cache.key": key[:100] + "..." if len(key) > 100 else key,
            }
        )
    
    @staticmethod
    def trace_cache_hit(span: Span, hit: bool) -> None:
        """Record cache hit/miss in span.
        
        Args:
            span: Cache span
            hit: Whether cache hit occurred
        """
        span.set_attributes({
            "cache.hit": hit,
            "cache.miss": not hit,
        })
    
    @staticmethod
    def trace_cache_size(span: Span, size_bytes: int) -> None:
        """Record cache size in span.
        
        Args:
            span: Cache span
            size_bytes: Cache size in bytes
        """
        span.set_attributes({
            "cache.size_bytes": size_bytes,
        })


class ExternalServiceTracer:
    """Helper for tracing external service calls."""
    
    @staticmethod
    def trace_http_request(
        tracer: Tracer,
        method: str,
        url: str,
        service_name: str,
        parent_span: Optional[Span] = None
    ) -> SpanContext:
        """Trace an HTTP request to external service.
        
        Args:
            tracer: Tracer instance
            method: HTTP method
            url: Request URL
            service_name: Target service name
            parent_span: Parent span
            
        Returns:
            Span context
        """
        return SpanContext(
            tracer=tracer,
            name=f"{service_name}.{method.lower()}",
            kind=SpanKind.CLIENT,
            attributes={
                "http.method": method,
                "http.url": url,
                "http.scheme": url.split("://")[0] if "://" in url else "",
                "http.target": url.split("://")[-1] if "://" in url else url,
                "peer.service": service_name,
                "peer.address": url,
            }
        )
    
    @staticmethod
    def trace_http_response(span: Span, status_code: int, response_size: int) -> None:
        """Record HTTP response in span.
        
        Args:
            span: HTTP span
            status_code: Response status code
            response_size: Response size in bytes
        """
        span.set_attributes({
            "http.status_code": status_code,
            "http.response_size": response_size,
        })
        
        if status_code >= 400:
            span.set_status(SpanStatus.ERROR, f"HTTP {status_code}")
        else:
            span.set_status(SpanStatus.OK)


class BusinessLogicTracer:
    """Helper for tracing business logic operations."""
    
    @staticmethod
    def trace_search_operation(
        tracer: Tracer,
        query: str,
        search_type: str,
        result_count: int,
        duration_ms: float,
        parent_span: Optional[Span] = None
    ) -> SpanContext:
        """Trace a search operation.
        
        Args:
            tracer: Tracer instance
            query: Search query
            search_type: Type of search
            result_count: Number of results
            duration_ms: Operation duration
            parent_span: Parent span
            
        Returns:
            Span context
        """
        span = tracer.start_span(
            name=f"search.{search_type}",
            kind=SpanKind.INTERNAL,
            attributes={
                "search.query": query[:100] + "..." if len(query) > 100 else query,
                "search.type": search_type,
                "search.result_count": result_count,
                "search.duration_ms": duration_ms,
            },
            parent_context=parent_span.trace_context if parent_span else None
        )
        
        span.end()
        return span
    
    @staticmethod
    def trace_ingestion_operation(
        tracer: Tracer,
        source_id: str,
        entities_processed: int,
        relationships_processed: int,
        duration_ms: float,
        parent_span: Optional[Span] = None
    ) -> SpanContext:
        """Trace an ingestion operation.
        
        Args:
            tracer: Tracer instance
            source_id: Source document ID
            entities_processed: Number of entities processed
            relationships_processed: Number of relationships processed
            duration_ms: Operation duration
            parent_span: Parent span
            
        Returns:
            Span context
        """
        span = tracer.start_span(
            name="ingestion.process",
            kind=SpanKind.INTERNAL,
            attributes={
                "ingestion.source_id": source_id,
                "ingestion.entities_processed": entities_processed,
                "ingestion.relationships_processed": relationships_processed,
                "ingestion.duration_ms": duration_ms,
                "ingestion.total_items": entities_processed + relationships_processed,
            },
            parent_context=parent_span.trace_context if parent_span else None
        )
        
        span.end()
        return span


# FastAPI dependencies
def get_current_span_dependency():
    """FastAPI dependency to get current span.
    
    Returns:
        Current span or None
    """
    def dependency(request: Request) -> Optional[Span]:
        return getattr(request.state, "span", None)
    return dependency


def get_trace_context_dependency():
    """FastAPI dependency to get current trace context.
    
    Returns:
        Current trace context or None
    """
    def dependency(request: Request) -> Optional["TraceContext"]:
        return getattr(request.state, "trace_context", None)
    return dependency


def get_trace_id_dependency():
    """FastAPI dependency to get current trace ID.
    
    Returns:
        Current trace ID or None
    """
    def dependency(request: Request) -> Optional[str]:
        span = getattr(request.state, "span", None)
        return span.trace_context.trace_id if span else None
    return dependency


# Initialize tracing on import
tracer = get_tracer()
