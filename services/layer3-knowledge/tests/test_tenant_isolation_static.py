"""Static tenant-isolation gates for Layer 3 Neo4j Cypher usage."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_layer3_cypher_scope_static_guard_passes() -> None:
    """The repository must not contain unscoped Layer 3 tenant-owned Cypher paths."""

    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "check_layer3_cypher_scope.py"

    migrated_roots = [
        "services/layer3-knowledge/src/analytics",
        "services/layer3-knowledge/src/retrieval",
        "value_fabric/layer3/analytics",
        "value_fabric/layer3/retrieval",
    ]

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(repo_root),
            "--paths",
            *migrated_roots,
            "--warnings-as-errors",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 error(s)" in result.stdout
    assert "0 warning(s)" in result.stdout
