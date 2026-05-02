"""Local pytest bootstrap for package-adjacent canonical contract tests."""

from __future__ import annotations

import sys
from pathlib import Path

PYTHON_SRC = Path(__file__).resolve().parents[1]
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))
