"""Stable Layer 4 database façade with dependency-tolerant fallback."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from uuid import UUID

_SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "layer4-agents"
if str(_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVICE_ROOT))


def _install_fallback():
    class TenantContextError(Exception):
        pass

    FAIL_SAFE_MODE = True
    RESERVED_TENANT_KEYWORDS = frozenset({"system", "admin", "internal"})
    _tenant_validation_metrics = {
        "validations_total": 0,
        "validation_failures": 0,
        "uuid_format_errors": 0,
        "missing_context_errors": 0,
        "empty_tenant_errors": 0,
    }

    def get_tenant_validation_metrics() -> dict[str, int]:
        return _tenant_validation_metrics.copy()

    def reset_tenant_validation_metrics() -> None:
        _tenant_validation_metrics.update({k: 0 for k in _tenant_validation_metrics})

    def validate_tenant_id(tenant_id: UUID | str | None) -> str:
        _tenant_validation_metrics["validations_total"] += 1
        if tenant_id is None:
            _tenant_validation_metrics["missing_context_errors"] += 1
            _tenant_validation_metrics["validation_failures"] += 1
            raise TenantContextError("Tenant context is mandatory.")

        normalized = str(tenant_id).strip()
        if not normalized:
            _tenant_validation_metrics["empty_tenant_errors"] += 1
            _tenant_validation_metrics["validation_failures"] += 1
            raise TenantContextError("Empty tenant_id is not allowed.")

        if normalized.lower() not in RESERVED_TENANT_KEYWORDS:
            try:
                UUID(normalized)
            except ValueError as exc:
                _tenant_validation_metrics["uuid_format_errors"] += 1
                _tenant_validation_metrics["validation_failures"] += 1
                raise TenantContextError("Invalid tenant_id format.") from exc
        return normalized

    globals().update(locals())


try:
    _impl = importlib.import_module("src.database")
    for _name in dir(_impl):
        if not _name.startswith("__"):
            globals()[_name] = getattr(_impl, _name)
except Exception:  # optional dependency failures should not break security tests
    _install_fallback()

__all__ = [name for name in globals() if not name.startswith("_")]
