"""Prometheus metrics collection for Layer 4 Agentic Workflow Engine."""

import time
from typing import Dict, List, Optional, Any
from functools import wraps

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

import logging

logger = logging.getLogger(__name__)


class MetricsConfig:
    """Configuration for metrics collection."""

    def __init__(
        self,
        enabled: bool = True,
        registry: Optional[CollectorRegistry] = None,
        prefix: str = "layer4_",
        label_namespace: str = "agents",
        default_buckets: Optional[List[float]] = None,
    ):
        self.enabled = enabled
        self.registry = registry or CollectorRegistry()
        self.prefix = prefix
        self.label_namespace = label_namespace
        self.default_buckets = default_buckets or [0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0]


class PrometheusMetrics:
    """Prometheus metrics collector for Layer 4."""

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

        # Workflow metrics
        self._metrics["workflow_executions_total"] = Counter(
            f"{prefix}workflow_executions_total",
            "Total workflow executions",
            ["workflow_type", "status"],
            registry=self.config.registry
        )

        self._metrics["workflow_duration"] = Histogram(
            f"{prefix}workflow_duration_seconds",
            "Workflow execution duration",
            ["workflow_type"],
            buckets=self.config.default_buckets,
            registry=self.config.registry
        )

        # Agent/tool metrics
        self._metrics["agent_calls_total"] = Counter(
            f"{prefix}agent_calls_total",
            "Total agent/tool calls",
            ["agent_type", "status"],
            registry=self.config.registry
        )

        self._metrics["agent_call_duration"] = Histogram(
            f"{prefix}agent_call_duration_seconds",
            "Agent call duration",
            ["agent_type"],
            buckets=self.config.default_buckets,
            registry=self.config.registry
        )

        # Active connections gauge
        self._metrics["active_connections"] = Gauge(
            f"{prefix}active_connections",
            "Number of active connections",
            ["connection_type"],
            registry=self.config.registry
        )

        # Health status gauge (for alerting)
        self._metrics["health_status"] = Gauge(
            f"{prefix}health_status",
            "Health status (1=healthy, 0=unhealthy)",
            ["component"],
            registry=self.config.registry
        )
        # Initialize with healthy status
        self._metrics["health_status"].labels(component="api").set(1)

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
            "version": "0.2.0",
            "service": "layer4-agents"
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

    def increment_workflow_executions(self, workflow_type: str, status: str) -> None:
        if self.config.enabled:
            self._metrics["workflow_executions_total"].labels(
                workflow_type=workflow_type, status=status
            ).inc()

    def observe_workflow_duration(self, duration: float, workflow_type: str) -> None:
        if self.config.enabled:
            self._metrics["workflow_duration"].labels(
                workflow_type=workflow_type
            ).observe(duration)

    def increment_agent_calls(self, agent_type: str, status: str) -> None:
        if self.config.enabled:
            self._metrics["agent_calls_total"].labels(
                agent_type=agent_type, status=status
            ).inc()

    def observe_agent_call_duration(self, duration: float, agent_type: str) -> None:
        if self.config.enabled:
            self._metrics["agent_call_duration"].labels(
                agent_type=agent_type
            ).observe(duration)

    def set_active_connections(self, count: int, connection_type: str = "total") -> None:
        if self.config.enabled:
            self._metrics["active_connections"].labels(
                connection_type=connection_type
            ).set(count)

    def set_health_status(self, healthy: bool, component: str = "api") -> None:
        """Set health status gauge (1=healthy, 0=unhealthy)."""
        if self.config.enabled:
            status = 1 if healthy else 0
            self._metrics["health_status"].labels(component=component).set(status)

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

        # Get request size
        request_size = 0
        if hasattr(request, "headers") and "content-length" in request.headers:
            try:
                request_size = int(request.headers["content-length"])
            except (ValueError, TypeError):
                request_size = 0

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
    logger.info("Layer 4 Prometheus metrics initialized")
    return _metrics
