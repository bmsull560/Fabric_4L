"""Prometheus metrics collection for Layer 2 Extraction Pipeline."""

import time
from typing import Dict, List, Optional, Any
from functools import wraps

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Dummy classes for type hints
    class CollectorRegistry: pass
    class Counter: pass
    class Histogram: pass
    class Gauge: pass
    class Info: pass

import logging

logger = logging.getLogger(__name__)


class MetricsConfig:
    """Configuration for metrics collection."""

    def __init__(
        self,
        enabled: bool = True,
        registry: Optional[CollectorRegistry] = None,
        prefix: str = "layer2_",
        label_namespace: str = "extraction",
        default_buckets: Optional[List[float]] = None,
    ):
        self.enabled = enabled and PROMETHEUS_AVAILABLE
        self.registry = registry or CollectorRegistry() if PROMETHEUS_AVAILABLE else None
        self.prefix = prefix
        self.label_namespace = label_namespace
        self.default_buckets = default_buckets or [0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0]


class PrometheusMetrics:
    """Prometheus metrics collector for Layer 2."""

    def __init__(self, config: Optional[MetricsConfig] = None):
        if not PROMETHEUS_AVAILABLE:
            raise ImportError("prometheus_client library is required")
        self.config = config or MetricsConfig()
        self._metrics: Dict[str, Any] = {}
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Setup all Prometheus metrics."""
        prefix = self.config.prefix

        # HTTP request metrics
        self._metrics["requests_total"] = Counter(
            f"{prefix}http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=self.config.registry
        )

        self._metrics["request_duration"] = Histogram(
            f"{prefix}http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
            buckets=self.config.default_buckets,
            registry=self.config.registry
        )

        # Extraction-specific metrics
        self._metrics["extraction_jobs_total"] = Counter(
            f"{prefix}extraction_jobs_total",
            "Total extraction jobs",
            ["status"],
            registry=self.config.registry
        )

        self._metrics["extraction_duration"] = Histogram(
            f"{prefix}extraction_duration_seconds",
            "Extraction job duration",
            buckets=self.config.default_buckets,
            registry=self.config.registry
        )

        self._metrics["entities_extracted_total"] = Counter(
            f"{prefix}entities_extracted_total",
            "Total entities extracted",
            ["entity_type"],
            registry=self.config.registry
        )

        self._metrics["relationships_extracted_total"] = Counter(
            f"{prefix}relationships_extracted_total",
            "Total relationships extracted",
            registry=self.config.registry
        )

        self._metrics["chunks_processed_total"] = Counter(
            f"{prefix}chunks_processed_total",
            "Total chunks processed",
            registry=self.config.registry
        )

        # Active connections
        self._metrics["active_connections"] = Gauge(
            f"{prefix}active_connections",
            "Number of active connections",
            ["connection_type"],
            registry=self.config.registry
        )

        # Error metrics
        self._metrics["errors_total"] = Counter(
            f"{prefix}errors_total",
            "Total errors",
            ["error_type", "component"],
            registry=self.config.registry
        )

        # Build info
        self._metrics["build_info"] = Info(
            f"{prefix}build_info",
            "Build information",
            registry=self.config.registry
        )
        self._metrics["build_info"].info({
            "version": "1.0.0",
            "service": "layer2-extraction"
        })

    def increment_requests_total(self, method: str, endpoint: str, status_code: int) -> None:
        if self.config.enabled:
            self._metrics["requests_total"].labels(
                method=method, endpoint=endpoint, status_code=str(status_code)
            ).inc()

    def observe_request_duration(self, duration: float, method: str, endpoint: str) -> None:
        if self.config.enabled:
            self._metrics["request_duration"].labels(
                method=method, endpoint=endpoint
            ).observe(duration)

    def increment_extraction_jobs(self, status: str) -> None:
        if self.config.enabled:
            self._metrics["extraction_jobs_total"].labels(status=status).inc()

    def observe_extraction_duration(self, duration: float) -> None:
        if self.config.enabled:
            self._metrics["extraction_duration"].observe(duration)

    def increment_entities_extracted(self, count: int, entity_type: str) -> None:
        if self.config.enabled:
            self._metrics["entities_extracted_total"].labels(entity_type=entity_type).inc(count)

    def increment_relationships_extracted(self, count: int) -> None:
        if self.config.enabled:
            self._metrics["relationships_extracted_total"].inc(count)

    def increment_chunks_processed(self, count: int) -> None:
        if self.config.enabled:
            self._metrics["chunks_processed_total"].inc(count)

    def set_active_connections(self, count: int, connection_type: str = "total") -> None:
        if self.config.enabled:
            self._metrics["active_connections"].labels(connection_type=connection_type).set(count)

    def increment_errors(self, error_type: str, component: str) -> None:
        if self.config.enabled:
            self._metrics["errors_total"].labels(error_type=error_type, component=component).inc()

    def get_metrics(self) -> str:
        """Get Prometheus metrics output."""
        if not self.config.enabled:
            return ""
        return generate_latest(self.config.registry).decode("utf-8")


class MetricsMiddleware:
    """Middleware to collect HTTP request metrics."""

    def __init__(self, metrics: PrometheusMetrics):
        self.metrics = metrics

    async def __call__(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        endpoint = request.url.path
        if endpoint.endswith("/"):
            endpoint = endpoint[:-1]
        if not endpoint:
            endpoint = "/"

        self.metrics.increment_requests_total(
            method=request.method, endpoint=endpoint, status_code=response.status_code
        )
        self.metrics.observe_request_duration(
            duration=duration, method=request.method, endpoint=endpoint
        )

        if response.status_code >= 400:
            error_type = "client_error" if response.status_code < 500 else "server_error"
            self.metrics.increment_errors(error_type=error_type, component="http")

        return response


_metrics: Optional[PrometheusMetrics] = None


def get_metrics() -> Optional[PrometheusMetrics]:
    return _metrics


def initialize_metrics(config: Optional[MetricsConfig] = None) -> Optional[PrometheusMetrics]:
    global _metrics
    if not PROMETHEUS_AVAILABLE:
        logger.warning("prometheus_client not available, metrics disabled")
        _metrics = None
        return None
    _metrics = PrometheusMetrics(config)
    logger.info("Layer 2 Prometheus metrics initialized")
    return _metrics
