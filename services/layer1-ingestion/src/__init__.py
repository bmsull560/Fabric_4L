"""Namespace bridge to the Layer 1 ingestion service ``src`` package.

All submodule lookups under ``value_fabric.layer1`` resolve to
``services/layer1-ingestion/src/`` so the canonical namespace stays in sync
with the maintained service tree.
"""

from __future__ import annotations

from pathlib import Path

_SERVICE_SRC = Path(__file__).resolve().parents[2] / "services" / "layer1-ingestion" / "src"
__path__ = [str(_SERVICE_SRC)]
