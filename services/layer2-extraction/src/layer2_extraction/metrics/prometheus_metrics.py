"""Prometheus metrics for Layer 2 extraction."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class MetricsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    port: int = 9090
    endpoint: str = "/metrics"


class PrometheusMetrics:
    """Prometheus metrics collector for LLM cost tracking."""

    def __init__(self, config: MetricsConfig | None = None) -> None:
        self.config = config or MetricsConfig()
        self._accumulated_costs: dict[tuple[str, str, str], float] = {}

    def record_llm_cost(
        self,
        provider: str,
        model: str,
        tenant_id: str,
        cost_usd: float,
    ) -> None:
        """Record LLM cost for a provider/model/tenant combination."""
        key = (provider, model, tenant_id)
        self._accumulated_costs[key] = self._accumulated_costs.get(key, 0.0) + cost_usd

    def get_accumulated_cost(self, provider: str, model: str, tenant_id: str) -> float:
        """Get accumulated cost for a provider/model/tenant combination."""
        return self._accumulated_costs.get((provider, model, tenant_id), 0.0)


_metrics_instance: PrometheusMetrics | None = None


def initialize_metrics(config: MetricsConfig | None = None) -> PrometheusMetrics:
    """Initialize and return the global PrometheusMetrics instance."""
    global _metrics_instance
    _metrics_instance = PrometheusMetrics(config=config)
    return _metrics_instance


def get_metrics() -> PrometheusMetrics | None:
    """Get the global PrometheusMetrics instance."""
    return _metrics_instance
