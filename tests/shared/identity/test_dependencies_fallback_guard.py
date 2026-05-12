from __future__ import annotations

import builtins
import importlib.util
import logging
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

DEPENDENCIES_FILE = Path("value_fabric/shared/identity/dependencies.py")


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, DEPENDENCIES_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _with_fastapi_missing(monkeypatch: pytest.MonkeyPatch):
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "fastapi" or name.startswith("fastapi."):
            raise ModuleNotFoundError("simulated fastapi missing for fallback tests")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ["VALUE_FABRIC_ENV", "ENV", "ENVIRONMENT", "APP_ENV", "CI", "ALLOW_IDENTITY_DEPENDENCY_FALLBACK_IN_CI", "ALLOW_IDENTITY_DEPENDENCY_FALLBACK", "PYTEST_CURRENT_TEST"]:
        monkeypatch.delenv(key, raising=False)


def test_fallback_disallowed_in_production_like_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    _with_fastapi_missing(monkeypatch)
    monkeypatch.setenv("VALUE_FABRIC_ENV", "production")

    with pytest.raises(RuntimeError, match="fallback is disabled"):
        _load_module("test_identity_dependencies_prod")


def test_fallback_allowed_for_dev_runtime_emits_observability(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    _clear_env(monkeypatch)
    _with_fastapi_missing(monkeypatch)
    monkeypatch.setenv("VALUE_FABRIC_ENV", "development")

    import value_fabric.shared.audit as audit_module

    audit_mock = Mock(return_value=None)
    monkeypatch.setattr(audit_module, "emit_audit_event", audit_mock)
    caplog.set_level(logging.WARNING)

    module = _load_module("test_identity_dependencies_dev")

    assert callable(module.Depends)
    assert any("fallback activated" in record.message for record in caplog.records)
    audit_mock.assert_called_once()


def test_fallback_allowed_in_ci_only_when_explicitly_opted_in(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    _with_fastapi_missing(monkeypatch)
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("ALLOW_IDENTITY_DEPENDENCY_FALLBACK_IN_CI", "true")

    module = _load_module("test_identity_dependencies_ci")

    assert callable(module.Depends)
