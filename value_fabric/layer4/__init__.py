"""Redirect shim: value_fabric.layer4.* -> services/layer4-agents/src/*.

Canonical Layer 4 code lives exclusively in ``services/layer4-agents/src/``.
This shim prepends that directory to ``__path__`` so that
``import value_fabric.layer4.engine`` resolves to the canonical tree
without duplicating source files.
"""

from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent.parent
_canonical = str(_repo_root / "services" / "layer4-agents" / "src")

if _canonical not in __path__:
    __path__.insert(0, _canonical)
