"""CI gate: no new routes that read body.tenant_id without calling
enforce_authenticated_tenant (F-15 regression guard).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ci" / "check_tenant_enforcement_opt_in.py"


def test_no_new_tenant_enforcement_opt_in_violations() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        "New tenant enforcement opt-in violations detected.\n"
        + result.stdout
        + result.stderr
    )
    assert "PASS" in result.stdout
