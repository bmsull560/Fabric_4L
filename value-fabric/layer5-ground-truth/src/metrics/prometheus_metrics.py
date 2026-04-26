"""Prometheus metrics collection for Layer 5 Ground Truth."""

import logging
import time
from typing import Any

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

logger = logging.getLogger(__name__)


class MetricsConfig:
    """Configuration for metrics collection."""

    def __init__(
        self,
        enabled: bool = True,
        registry: CollectorRegistry | None = None,
        prefix: str = "layer5_",
        label_namespace: str = "ground_truth",
        default_buckets: list[float] | None = None,
    ):
        self.enabled = enabled
        self.registry = registry or CollectorRegistry()
        self.prefix = prefix
        self.label_namespace = label_namespace
        self.default_buckets = default_buckets or [
            0.1,
            0.25,
            0.5,
            1.0,
            2.5,
            5.0,
            10.0,
            25.0,
            50.0,
        ]


class PrometheusMetrics:
    """Prometheus metrics collector for Layer 5 Ground Truth."""

    def __init__(self, config: MetricsConfig | None = None):
        self.config = config or MetricsConfig()
        self._metrics: dict[str, Any] = {}
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Setup all Prometheus metrics."""
        prefix = self.config.prefix

        # HTTP request metrics
        self._metrics["requests_total"] = Counter(
            f"{prefix}http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=self.config.registry,
        )

        self._metrics["request_duration"] = Histogram(
            f"{prefix}http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
            buckets=self.config.default_buckets,
            registry=self.config.registry,
        )

        # Truth object metrics
        self._metrics["truth_objects_total"] = Counter(
            f"{prefix}truth_objects_total",
            "Total truth objects created",
            ["claim_type", "status"],
            registry=self.config.registry,
        )

        self._metrics["validations_total"] = Counter(
            f"{prefix}validations_total",
            "Total validation state transitions",
            ["from_status", "to_status"],
            registry=self.config.registry,
        )

        self._metrics["truth_objects_by_status"] = Gauge(
            f"{prefix}truth_objects_by_status",
            "Current truth objects by status",
            ["status", "claim_type"],
            registry=self.config.registry,
        )

        self._metrics["sources_added_total"] = Counter(
            f"{prefix}sources_added_total",
            "Total evidence sources added",
            registry=self.config.registry,
        )

        self._metrics["kg_sync_total"] = Counter(
            f"{prefix}kg_sync_total",
            "Total knowledge graph sync operations",
            ["status"],
            registry=self.config.registry,
        )

        self._metrics["freshness_checks_total"] = Counter(
            f"{prefix}freshness_checks_total",
            "Total freshness monitoring checks",
            registry=self.config.registry,
        )

        self._metrics["stale_objects_detected"] = Counter(
            f"{prefix}stale_objects_detected",
            "Total stale objects detected",
            registry=self.config.registry,
        )

        # Active connections
        self._metrics["active_connections"] = Gauge(
            f"{prefix}active_connections",
            "Number of active connections",
            ["connection_type"],
            registry=self.config.registry,
        )

        # Health status gauge (for alerting)
        self._metrics["health_status"] = Gauge(
            f"{prefix}health_status",
            "Health status (1=healthy, 0=unhealthy)",
            ["component"],
            registry=self.config.registry,
        )
        # Initialize with healthy status
        self._metrics["health_status"].labels(component="api").set(1)
        self._metrics["health_status"].labels(component="database").set(1)
        self._metrics["health_status"].labels(component="layer3").set(1)

        # Error metrics
        self._metrics["errors_total"] = Counter(
            f"{prefix}errors_total",
            "Total errors",
            ["error_type", "component"],
            registry=self.config.registry,
        )

        # Build info
        self._metrics["build_info"] = Info(
            f"{prefix}build_info", "Build information", registry=self.config.registry
        )
        self._metrics["build_info"].info(
            {"version": "0.1.0", "service": "layer5-ground-truth"}
        )

    def increment_requests_total(
        self, method: str, endpoint: str, status_code: int
    ) -> None:
        if self.config.enabled:
            self._metrics["requests_total"].labels(
                method=method, endpoint=endpoint, status_code=str(status_code)
            ).inc()

    def observe_request_duration(
        self, duration: float, method: str, endpoint: str
    ) -> None:
        if self.config.enabled:
            self._metrics["request_duration"].labels(
                method=method, endpoint=endpoint
            ).observe(duration)

    def increment_truth_objects(self, claim_type: str, status: str) -> None:
        if self.config.enabled:
            self._metrics["truth_objects_total"].labels(
                claim_type=claim_type, status=status
            ).inc()

    def increment_validations(self, from_status: str, to_status: str) -> None:
        if self.config.enabled:
            self._metrics["validations_total"].labels(
                from_status=from_status, to_status=to_status
            ).inc()

    def set_truth_objects_by_status(
        self, status: str, claim_type: str, count: int
    ) -> None:
        if self.config.enabled:
            self._metrics["truth_objects_by_status"].labels(
                status=status, claim_type=claim_type
            ).set(count)

    def increment_sources_added(self) -> None:
        if self.config.enabled:
            self._metrics["sources_added_total"].inc()

    def increment_kg_sync(self, status: str) -> None:
        if self.config.enabled:
            self._metrics["kg_sync_total"].labels(status=status).inc()

    def increment_freshness_checks(self) -> None:
        if self.config.enabled:
            self._metrics["freshness_checks_total"].inc()

    def increment_stale_objects_detected(self) -> None:
        if self.config.enabled:
            self._metrics["stale_objects_detected"].inc()

    def set_health_status(self, healthy: bool, component: str = "api") -> None:
        if self.config.enabled:
            self._metrics["health_status"].labels(component=component).set(
                1 if healthy else 0
            )

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
    """ASGI middleware to collect HTTP request metrics."""

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


_metrics: PrometheusMetrics | None = None


def get_metrics() -> PrometheusMetrics | None:
    return _metrics


def initialize_metrics(config: MetricsConfig | None = None) -> PrometheusMetrics | None:
    global _metrics
    _metrics = PrometheusMetrics(config)
    logger.info("Layer 5 Prometheus metrics initialized")
    return _metrics
