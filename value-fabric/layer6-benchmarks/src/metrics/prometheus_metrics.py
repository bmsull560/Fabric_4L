"""Prometheus metrics collection for Layer 6 Benchmark Service."""

import logging
from typing import Any, Dict, List, Optional

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Info, generate_latest

logger = logging.getLogger(__name__)


class MetricsConfig:
    """Configuration for metrics collection."""

    def __init__(
        self,
        enabled: bool = True,
        registry: Optional[CollectorRegistry] = None,
        prefix: str = "layer6_",
        label_namespace: str = "benchmarks",
        default_buckets: Optional[List[float]] = None,
    ):
        self.enabled = enabled
        self.registry = registry or CollectorRegistry()
        self.prefix = prefix
        self.label_namespace = label_namespace
        self.default_buckets = default_buckets or [0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0]


class PrometheusMetrics:
    """Prometheus metrics collector for Layer 6 Benchmark Service."""

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
            registry=self.config.registry,
        )

        self._metrics["request_duration"] = Histogram(
            f"{prefix}http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
            buckets=self.config.default_buckets,
            registry=self.config.registry,
        )

        # Benchmark-specific metrics
        self._metrics["comparisons_total"] = Counter(
            f"{prefix}comparisons_total",
            "Total benchmark comparisons performed",
            ["dataset_id", "industry"],
            registry=self.config.registry,
        )

        self._metrics["validations_total"] = Counter(
            f"{prefix}validations_total",
            "Total benchmark validations performed",
            ["dataset_id", "result"],
            registry=self.config.registry,
        )

        self._metrics["datasets_loaded"] = Gauge(
            f"{prefix}datasets_loaded",
            "Number of benchmark datasets currently loaded",
            registry=self.config.registry,
        )

        self._metrics["comparison_duration"] = Histogram(
            f"{prefix}comparison_duration_seconds",
            "Comparison operation duration",
            buckets=self.config.default_buckets,
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
        self._metrics["build_info"].info({"version": "1.0.0", "service": "layer6-benchmarks"})

    def increment_requests_total(self, method: str, endpoint: str, status_code: int) -> None:
        if self.config.enabled:
            self._metrics["requests_total"].labels(
                method=method, endpoint=endpoint, status_code=str(status_code)
            ).inc()

    def observe_request_duration(self, duration: float, method: str, endpoint: str) -> None:
        if self.config.enabled:
            self._metrics["request_duration"].labels(method=method, endpoint=endpoint).observe(
                duration
            )

    def increment_comparisons(self, dataset_id: str, industry: str) -> None:
        if self.config.enabled:
            self._metrics["comparisons_total"].labels(
                dataset_id=dataset_id, industry=industry
            ).inc()

    def increment_validations(self, dataset_id: str, result: str) -> None:
        if self.config.enabled:
            self._metrics["validations_total"].labels(dataset_id=dataset_id, result=result).inc()

    def set_datasets_loaded(self, count: int) -> None:
        if self.config.enabled:
            self._metrics["datasets_loaded"].set(count)

    def observe_comparison_duration(self, duration: float) -> None:
        if self.config.enabled:
            self._metrics["comparison_duration"].observe(duration)

    def set_health_status(self, healthy: bool, component: str = "api") -> None:
        if self.config.enabled:
            self._metrics["health_status"].labels(component=component).set(1 if healthy else 0)

    def increment_errors(self, error_type: str, component: str) -> None:
        if self.config.enabled:
            self._metrics["errors_total"].labels(error_type=error_type, component=component).inc()

    def get_metrics(self) -> str:
        """Get Prometheus metrics output."""
        if not self.config.enabled:
            return ""
        return generate_latest(self.config.registry).decode("utf-8")


_metrics: Optional[PrometheusMetrics] = None


def get_metrics() -> Optional[PrometheusMetrics]:
    return _metrics


def initialize_metrics(config: Optional[MetricsConfig] = None) -> Optional[PrometheusMetrics]:
    global _metrics
    _metrics = PrometheusMetrics(config)
    logger.info("Layer 6 Prometheus metrics initialized")
    return _metrics


class MetricsMiddleware:
    """FastAPI middleware for collecting Prometheus HTTP metrics."""

    def __init__(self, metrics: PrometheusMetrics):
        self.metrics = metrics

    async def __call__(self, request, call_next):
        """Process request and collect metrics."""
        import time

        start_time = time.time()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time

            # Normalize endpoint path
            endpoint = request.url.path
            if endpoint.endswith("/"):
                endpoint = endpoint[:-1]
            if not endpoint:
                endpoint = "/"

            # Record metrics
            self.metrics.increment_requests_total(
                method=request.method,
                endpoint=endpoint,
                status_code=status_code
            )
            self.metrics.observe_request_duration(
                duration=duration,
                method=request.method,
                endpoint=endpoint
            )

            # Track errors
            if status_code >= 400:
                error_type = "client_error" if status_code < 500 else "server_error"
                self.metrics.increment_errors(error_type=error_type, component="http")

        return response

    async def dispatch(self, request, call_next):
        """Starlette-compatible dispatch method."""
        return await self.__call__(request, call_next)
