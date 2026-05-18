"""Allowed service-local exception for Layer 3 service wrapper.

Owner: layer3-knowledge
Removal/migration target: 2026-09-30
Reason: Service-local implementation permitted by runtime path governance.
"""
from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

from value_fabric.shared.identity.protocols import MetricsAccessHook


def _resolve_shared_src() -> Path | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "packages" / "shared" / "src"
        if candidate.exists():
            return candidate
    return None


_SHARED_SRC = _resolve_shared_src()
if _SHARED_SRC and str(_SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(_SHARED_SRC))

_observability = import_module("value_fabric.shared.observability.metrics_access")
verify_metrics_access: MetricsAccessHook = _observability.verify_metrics_access
