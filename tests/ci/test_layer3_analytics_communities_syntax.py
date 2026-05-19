"""CI syntax gate for Layer 3 analytics communities module."""

from __future__ import annotations

import py_compile
from pathlib import Path


def test_layer3_communities_module_compiles() -> None:
    """Ensure the communities module is syntax-valid and import-safe.

    value_fabric/layer3 is a path-redirect shim; the canonical source lives
    at services/layer3-knowledge/src/analytics/communities.py.
    """
    # Canonical path via the redirect-shim architecture
    module_path = Path("services/layer3-knowledge/src/analytics/communities.py")
    py_compile.compile(str(module_path), doraise=True)
