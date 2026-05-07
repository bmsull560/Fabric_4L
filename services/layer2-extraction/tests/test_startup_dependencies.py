import pytest

from layer2_extraction.startup_dependencies import verify_startup_dependencies


def test_layer2_dependency_gate_fail_closed_in_production(monkeypatch):
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    with pytest.raises(RuntimeError, match="redis"):
        verify_startup_dependencies(environment="production")


def test_layer2_dependency_gate_permissive_in_development(monkeypatch):
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    verify_startup_dependencies(environment="development")
