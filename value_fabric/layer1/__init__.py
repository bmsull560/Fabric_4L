"""Canonical Layer 1 import namespace.

Layer 1 callers must import runtime modules through ``value_fabric.layer1.*``.
During the runtime-path migration, this package still appends the
service-wrapper tree at ``services/layer1-ingestion/src`` to ``__path__`` so
canonical imports continue to resolve while modules move under this namespace.

Keep service-local imports compatibility-only. New runtime callers should not
import directly from ``services/layer1-ingestion/src``.
"""

from __future__ import annotations

from pathlib import Path

_repo_root: Path = Path(__file__).resolve().parent.parent.parent
_canonical: str = str(_repo_root / "services" / "layer1-ingestion" / "src")

# Only register the canonical path if it exists; fail fast otherwise.
if (_repo_root / "services" / "layer1-ingestion" / "src").exists():
    if _canonical not in __path__:
        __path__.append(_canonical)
else:
    raise FileNotFoundError(
        f"Canonical Layer 1 source tree not found at {_canonical}. "
        "Expected services/layer1-ingestion/src/ to exist."
    )
