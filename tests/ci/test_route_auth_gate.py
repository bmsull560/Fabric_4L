from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_SCRIPT = REPO_ROOT / "scripts/ci/check_route_auth_dependencies.py"


def test_route_auth_gate_scans_services_api_by_default() -> None:
    content = GATE_SCRIPT.read_text()

    assert "services/api/app/main.py" in content
    assert '"routers"' in content


def test_route_auth_gate_passes_for_services_api_routes() -> None:
    result = subprocess.run(
        [
            "python",
            str(GATE_SCRIPT),
            "--target",
            "services/api/app/main.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: all non-allowlisted routes have auth dependencies" in result.stdout
