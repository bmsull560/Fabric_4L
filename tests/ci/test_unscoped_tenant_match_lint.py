from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_unscoped_tenant_match_lint_passes() -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "ci" / "check_unscoped_tenant_match.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, cwd=root)
    assert result.returncode == 0, result.stdout + result.stderr
