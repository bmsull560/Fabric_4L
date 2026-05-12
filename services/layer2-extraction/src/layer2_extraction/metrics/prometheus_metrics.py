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

    def record_llm_tokens(
        self,
        provider: str,
        model: str,
        token_type: str,
        count: int,
    ) -> None:
        """Record LLM token count for a provider/model/token_type combination."""
        key = (provider, model, token_type)
        self._token_counts: dict[tuple[str, str, str], int] = getattr(self, "_token_counts", {})
        self._token_counts[key] = self._token_counts.get(key, 0) + count

    def get_metrics(self) -> str:
        """Generate Prometheus exposition format output."""
        lines: list[str] = []
        for (provider, model, tenant_id), cost in self._accumulated_costs.items():
            lines.append(
                f'vf_llm_cost_usd_total{{provider="{provider}",model="{model}",tenant_id="{tenant_id}"}} {cost}'
            )
        token_counts: dict[tuple[str, str, str], int] = getattr(self, "_token_counts", {})
        for (provider, model, token_type), count in token_counts.items():
            lines.append(
                f'vf_llm_tokens_total{{provider="{provider}",model="{model}",token_type="{token_type}"}} {count}'
            )
        return "\n".join(lines)


_metrics_instance: PrometheusMetrics | None = None


def initialize_metrics(config: MetricsConfig | None = None) -> PrometheusMetrics:
    """Initialize and return the global PrometheusMetrics instance."""
    global _metrics_instance
    _metrics_instance = PrometheusMetrics(config=config)
    return _metrics_instance


def get_metrics() -> PrometheusMetrics | None:
    """Get the global PrometheusMetrics instance."""
    return _metrics_instance
