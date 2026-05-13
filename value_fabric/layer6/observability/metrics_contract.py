"""Canonical Layer 6 benchmark service metrics contract."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricSpec:
    name: str
    description: str
    labels: tuple[str, ...]
    max_cardinality: dict[str, int]


LAYER6_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec(
        name="layer6_requests_total",
        description="Count of benchmark API requests processed.",
        labels=("route", "method", "status_class"),
        max_cardinality={"route": 20, "method": 8, "status_class": 5},
    ),
    MetricSpec(
        name="layer6_request_duration_seconds",
        description="Benchmark API request latency histogram.",
        labels=("route", "method"),
        max_cardinality={"route": 20, "method": 8},
    ),
    MetricSpec(
        name="layer6_dataset_comparisons_total",
        description="Count of compare operations by outcome.",
        labels=("industry", "outcome"),
        max_cardinality={"industry": 50, "outcome": 4},
    ),
)


def metric_names() -> set[str]:
    return {spec.name for spec in LAYER6_METRICS}
