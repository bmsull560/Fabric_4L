"""Namespace bridge to the Layer 1 ingestion service ``src`` package."""

from __future__ import annotations

from pathlib import Path

_SERVICE_SRC = Path(__file__).resolve().parents[3] / "services" / "layer1-ingestion" / "src"
__path__ = [str(_SERVICE_SRC)]
