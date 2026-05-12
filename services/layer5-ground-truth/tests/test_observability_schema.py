from pathlib import Path


REQUIRED_LOG_KEYS = (
    "request_id",
    "tenant_id",
    "truth_object_id",
    "transition",
    "sync_status",
)


def test_layer5_structured_log_keys_present_in_runtime_paths() -> None:
    """Guardrail: representative Layer 5 paths must emit required structured keys."""
    runtime_files = [
        Path("src/layer5_ground_truth/services/state_machine.py"),
        Path("src/layer5_ground_truth/integration/layer3_client.py"),
    ]
    for rel_path in runtime_files:
        content = (Path(__file__).resolve().parents[1] / rel_path).read_text()
        for key in REQUIRED_LOG_KEYS:
            assert f'"{key}"' in content, f"missing structured log key {key} in {rel_path}"


def test_layer5_observability_metric_schema_is_defined() -> None:
    """Guardrail: schema metric names/labels remain stable unless explicitly reviewed."""
    content = (
        Path(__file__).resolve().parents[1]
        / "src/metrics/prometheus_metrics.py"
    ).read_text()
    assert "validation_latency_seconds" in content
    assert "validation_transition_failures_total" in content
    assert "kg_sync_outcomes_total" in content
    assert '["transition"]' in content
    assert '["transition", "reason"]' in content
    assert '["sync_status", "transition"]' in content
