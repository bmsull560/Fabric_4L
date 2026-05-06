#!/usr/bin/env python3
"""Runtime migration pass for legacy shared imports."""

from __future__ import annotations

import runpy
from pathlib import Path

if __name__ == "__main__":
    script = Path(__file__).with_name("migrate_shared_imports_batch1.py")
    runpy.run_path(str(script), run_name="__main__")
