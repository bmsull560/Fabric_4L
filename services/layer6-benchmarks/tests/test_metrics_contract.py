import json
from pathlib import Path

CONTRACT = Path(__file__).resolve().parents[3] / "contracts" / "observability" / "layer6-metrics.json"


def _metrics() -> dict[str, dict]:
    payload = json.loads(CONTRACT.read_text())
    return {metric["name"]: metric for metric in payload["metrics"]}


def test_required_metrics_emitted_with_expected_labels() -> None:
    metrics = _metrics()
    assert metrics["layer6_requests_total"]["labels"] == ["route", "method", "status_class"]
    assert metrics["layer6_request_duration_seconds"]["labels"] == ["route", "method"]
    assert metrics["layer6_dataset_comparisons_total"]["labels"] == ["industry", "outcome"]


def test_metric_label_cardinality_constraints_are_bounded() -> None:
    for metric in _metrics().values():
        for label in metric["labels"]:
            assert label in metric["max_cardinality"]
            assert 0 < metric["max_cardinality"][label] <= 100
