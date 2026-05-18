from __future__ import annotations

import builtins
import importlib.util
import logging
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

DEPENDENCIES_FILE = Path("packages/shared/src/value_fabric/shared/identity/dependencies.py")
IDENTITY_DIR = DEPENDENCIES_FILE.parent
SECURITY_DIR = Path("packages/shared/src/value_fabric/shared/security")


def _load_module(name: str):
    _install_identity_package_stub()
    spec = importlib.util.spec_from_file_location(name, DEPENDENCIES_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _install_identity_package_stub() -> None:
    package_paths = {
        "value_fabric.shared.identity": IDENTITY_DIR,
        "value_fabric.shared.security": SECURITY_DIR,
    }
    for package_name, package_path in package_paths.items():
        if package_name in sys.modules:
            continue
        package = importlib.util.module_from_spec(
            importlib.util.spec_from_loader(package_name, loader=None, is_package=True)
        )
        package.__path__ = [str(package_path)]  # type: ignore[attr-defined]
        sys.modules[package_name] = package


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


def _with_fastapi_missing_and_audit_stub(monkeypatch: pytest.MonkeyPatch, audit_mock: Mock) -> None:
    _with_fastapi_missing(monkeypatch)
    audit_action = type("AuditAction", (), {"UNKNOWN": "unknown"})
    audit_outcome = type("AuditOutcome", (), {"ERROR": "error", "FAILURE": "failure"})
    audit_module = type("AuditModule", (), {"emit_audit_event": audit_mock})()
    audit_models_module = type(
        "AuditModelsModule",
        (),
        {"AuditAction": audit_action, "AuditOutcome": audit_outcome, "PrivilegedAccessDetails": object},
    )()
    monkeypatch.setitem(sys.modules, "value_fabric.shared.audit", audit_module)
    monkeypatch.setitem(sys.modules, "value_fabric.shared.audit.models", audit_models_module)


def test_fallback_disallowed_in_production_like_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    _with_fastapi_missing(monkeypatch)
    monkeypatch.setenv("VALUE_FABRIC_ENV", "production")

    with pytest.raises(RuntimeError, match="fallback is disabled"):
        _load_module("test_identity_dependencies_prod")


def test_fallback_allowed_for_dev_runtime_emits_observability(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    _clear_env(monkeypatch)
    audit_mock = Mock(return_value=None)
    _with_fastapi_missing_and_audit_stub(monkeypatch, audit_mock)
    monkeypatch.setenv("VALUE_FABRIC_ENV", "development")
    caplog.set_level(logging.WARNING)

    module = _load_module("test_identity_dependencies_dev")

    assert callable(module.Depends)
    assert any("fallback activated" in record.message for record in caplog.records)
    audit_mock.assert_called_once()


def test_fallback_allowed_in_ci_only_when_explicitly_opted_in(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    _clear_env(monkeypatch)
    audit_mock = Mock(return_value=None)
    _with_fastapi_missing_and_audit_stub(monkeypatch, audit_mock)
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("ALLOW_IDENTITY_DEPENDENCY_FALLBACK_IN_CI", "true")
    caplog.set_level(logging.WARNING)

    module = _load_module("test_identity_dependencies_ci")

    assert callable(module.Depends)
    assert any("fallback activated" in record.message for record in caplog.records)
    audit_mock.assert_called_once()
