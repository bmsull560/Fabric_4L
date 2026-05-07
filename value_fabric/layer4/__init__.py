"""Redirect shim: value_fabric.layer4.* -> services/layer4-agents/src/*.

Canonical Layer 4 code lives exclusively in ``services/layer4-agents/src/``.
This shim prepends that directory to ``__path__`` so that
``import value_fabric.layer4.engine`` resolves to the canonical tree
without duplicating source files.
"""

from pathlib import Path

_local_pkg: str = str(Path(__file__).resolve().parent)
if _local_pkg not in __path__:
    __path__.insert(0, _local_pkg)

_repo_root: Path = Path(__file__).resolve().parent.parent.parent
_canonical: str = str(_repo_root / "services" / "layer4-agents" / "src")

# Only register the canonical path if it exists; fail fast otherwise.
if (_repo_root / "services" / "layer4-agents" / "src").exists():
    if _canonical not in __path__:
        __path__.append(_canonical)
else:
    raise FileNotFoundError(
        f"Canonical Layer 4 source tree not found at {_canonical}. "
        "Expected services/layer4-agents/src/ to exist."
    )
