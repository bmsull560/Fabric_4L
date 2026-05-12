"""Redirect shim: value_fabric.layer1.* -> services/layer1-ingestion/src/*.

Canonical Layer 1 code lives exclusively in ``services/layer1-ingestion/src/``.
This shim appends that directory to ``__path__`` so that
``import value_fabric.layer1.adapters.base`` resolves to the canonical tree.
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
