"""Redirect shim: value_fabric.layer3.* -> services/layer3-knowledge/src/*.

Canonical Layer 3 code lives exclusively in ``services/layer3-knowledge/src/``.
This shim appends that directory to ``__path__`` so that
``import value_fabric.layer3.api.main`` resolves to the canonical tree.
"""

from __future__ import annotations

from pathlib import Path

_repo_root: Path = Path(__file__).resolve().parent.parent.parent
_canonical: str = str(_repo_root / "services" / "layer3-knowledge" / "src")

# Only register the canonical path if it exists; fail fast otherwise.
if (_repo_root / "services" / "layer3-knowledge" / "src").exists():
    if _canonical not in __path__:
        __path__.append(_canonical)
else:
    raise FileNotFoundError(
        f"Canonical Layer 3 source tree not found at {_canonical}. "
        "Expected services/layer3-knowledge/src/ to exist."
    )
