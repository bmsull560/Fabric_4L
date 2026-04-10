"""Prometheus metrics collection for Layer 1 Ingestion Service."""

import time
from typing import Dict, List, Optional, Any
from functools import wraps

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest

import logging

logger = logging.getLogger(__name__)


class MetricsConfig:
    """Configuration for metrics collection."""

    def __init__(
        self,
        enabled: bool = True,
        registry: Optional[CollectorRegistry] = None,
        prefix: str = "layer1_",
        label_namespace: str = "ingestion",
        default_buckets: Optional[List[float]] = None,
    ):
        self.enabled = enabled
        self.registry = registry or CollectorRegistry()
        self.prefix = prefix
        self.label_namespace = label_namespace
        self.default_buckets = default_buckets or [0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0]


class PrometheusMetrics:
    """Prometheus metrics collector for Layer 1."""

    def __init__(self, config: Optional[MetricsConfig] = None):
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

        # Ingestion-specific metrics
        self._metrics["ingestion_jobs_total"] = Counter(
            f"{prefix}ingestion_jobs_total",
            "Total ingestion jobs",
            ["status", "target_type"],
            registry=self.config.registry
        )

        self._metrics["ingestion_duration"] = Histogram(
            f"{prefix}ingestion_duration_seconds",
            "Ingestion job duration",
            ["target_type"],
            buckets=self.config.default_buckets,
            registry=self.config.registry
        )

        self._metrics["bytes_ingested_total"] = Counter(
            f"{prefix}bytes_ingested_total",
            "Total bytes ingested",
            ["source_type"],
            registry=self.config.registry
        )

        self._metrics["pages_crawled_total"] = Counter(
            f"{prefix}pages_crawled_total",
            "Total pages crawled",
            ["status"],
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
            "service": "layer1-ingestion"
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

    def increment_ingestion_jobs(self, status: str, target_type: str) -> None:
        if self.config.enabled:
            self._metrics["ingestion_jobs_total"].labels(
                status=status, target_type=target_type
            ).inc()

    def observe_ingestion_duration(self, duration: float, target_type: str) -> None:
        if self.config.enabled:
            self._metrics["ingestion_duration"].labels(
                target_type=target_type
            ).observe(duration)

    def increment_bytes_ingested(self, bytes_count: int, source_type: str) -> None:
        if self.config.enabled:
            self._metrics["bytes_ingested_total"].labels(
                source_type=source_type
            ).inc(bytes_count)

    def increment_pages_crawled(self, status: str) -> None:
        if self.config.enabled:
            self._metrics["pages_crawled_total"].labels(status=status).inc()

    def set_active_connections(self, count: int, connection_type: str = "total") -> None:
        if self.config.enabled:
            self._metrics["active_connections"].labels(
                connection_type=connection_type
            ).set(count)

    def increment_errors(self, error_type: str, component: str) -> None:
        if self.config.enabled:
            self._metrics["errors_total"].labels(
                error_type=error_type, component=component
            ).inc()

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
    _metrics = PrometheusMetrics(config)
    logger.info("Layer 1 Prometheus metrics initialized")
    return _metrics
