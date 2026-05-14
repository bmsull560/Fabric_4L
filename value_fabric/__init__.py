"""`value_fabric` namespace package bootstrap.

This repo keeps canonical `value_fabric.*` modules under package-local `src/`
directories. When working from a source checkout, add those namespace roots to
`value_fabric.__path__` so `import value_fabric.shared` resolves without
requiring a test runner or shell startup hook to mutate `sys.path`.
"""

from __future__ import annotations

import pkgutil
from pathlib import Path


def _append_namespace_root(candidate: Path, *, prioritize: bool = False) -> None:
    if not candidate.exists():
        return

    resolved = str(candidate.resolve())
    if resolved in __path__:
        if prioritize:
            __path__.remove(resolved)
            __path__.insert(0, resolved)
        return
    if prioritize:
        __path__.insert(0, resolved)
    else:
        __path__.append(resolved)


__path__ = pkgutil.extend_path(__path__, __name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_append_namespace_root(_REPO_ROOT / "packages" / "shared" / "src" / "value_fabric", prioritize=True)
# Per ADR-027, each layer's value_fabric/layerX/__init__.py shim appends its own
# service source path via __path__.append(). Do not duplicate those registrations
# here; they create redundant entries and mask shim-health problems.
