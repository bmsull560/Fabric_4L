"""Compatibility entrypoint for repository-level startup validation tests."""

from __future__ import annotations

import sys
from pathlib import Path

from value_fabric.shared.security.config import validate_all_controls

validate_all_controls()

_SERVICE_SRC = Path(__file__).resolve().parents[1] / "services" / "layer4-agents" / "src"
if str(_SERVICE_SRC) not in sys.path:
    sys.path.insert(0, str(_SERVICE_SRC))

from api.main import app

__all__ = ["app"]
