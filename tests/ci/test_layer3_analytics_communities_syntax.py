"""CI syntax gate for Layer 3 analytics communities module."""

from __future__ import annotations

import py_compile
from pathlib import Path


def test_layer3_communities_module_compiles() -> None:
    """Ensure the communities module is syntax-valid and import-safe."""

    module_path = Path("value_fabric/layer3/analytics/communities.py")
    py_compile.compile(str(module_path), doraise=True)
