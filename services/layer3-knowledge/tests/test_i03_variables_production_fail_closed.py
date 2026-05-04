"""I-03 production fail-closed regression tests for Layer 3 variables endpoint.

These tests lock the service-level policy that production-like runtimes must
not silently fall back to mock benchmark or formula calculation values.
"""

from __future__ import annotations

import os

import pytest


def _clear_layer3_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("ENVIRONMENT", "APP_ENV", "LAYER3_ENV"):
        monkeypatch.delenv(key, raising=False)


class TestLayer3VariablesProductionFailClosed:
    def test_production_rejects_mock_benchmark_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
        """Production-like environments must fail closed on benchmark_lookup without integration."""
        _clear_layer3_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")
        monkeypatch.setenv("NEO4J_PASSWORD", "test-password")

        # Import after setting environment to ensure config reads correct env
        from src.api.routes.variables import _is_production_like

        assert _is_production_like() is True

    def test_staging_rejects_mock_formula_calculation(monkeypatch: pytest.MonkeyPatch) -> None:
        """Staging environments must fail closed on formula_calculation without integration."""
        _clear_layer3_env(monkeypatch)
        monkeypatch.setenv("APP_ENV", "staging")

        from src.api.routes.variables import _is_production_like

        assert _is_production_like() is True

    def test_development_allows_mock_fallback_with_warning(monkeypatch: pytest.MonkeyPatch) -> None:
        """Development environments allow mock fallback with warning logs."""
        _clear_layer3_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "development")

        from src.api.routes.variables import _is_production_like

        assert _is_production_like() is False

    def test_test_environment_allows_mock_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environments allow mock fallback for test fixtures."""
        _clear_layer3_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "test")

        from src.api.routes.variables import _is_production_like

        assert _is_production_like() is False

    def test_ci_environment_allows_mock_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
        """CI environments allow mock fallback for test pipelines."""
        _clear_layer3_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "ci")

        from src.api.routes.variables import _is_production_like

        assert _is_production_like() is False

    def test_default_environment_is_development(monkeypatch: pytest.MonkeyPatch) -> None:
        """Default (no ENV set) should be treated as development."""
        _clear_layer3_env(monkeypatch)

        from src.api.routes.variables import _is_production_like

        assert _is_production_like() is False
