"""Shared utilities for Fabric_4L standalone scripts.

Provides helpers that every script in scripts/ should prefer over
hardcoded paths or duplicated boilerplate.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TextIO


# ---------------------------------------------------------------------------
# Repository root resolution
# ---------------------------------------------------------------------------


def resolve_repo_root(cwd: Path | None = None) -> Path:
    """Return the absolute path to the Fabric_4L repository root.

    Tries, in order:
    1. The ``FABRIC_4L_ROOT`` environment variable.
    2. Git root from the current working directory.
    3. Two parents above this file (``scripts/_lib.py``).

    Raises ``RuntimeError`` if none of the strategies succeed.
    """
    env_root = os.getenv("FABRIC_4L_ROOT")
    if env_root:
        path = Path(env_root).resolve()
        if path.is_dir():
            return path

    start = cwd or Path.cwd()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(start),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            git_root = Path(result.stdout.strip()).resolve()
            if git_root.is_dir():
                return git_root
    except FileNotFoundError:
        pass  # git not in PATH

    fallback = Path(__file__).resolve().parents[1]
    if (fallback / "README.md").exists() or (fallback / "package.json").exists():
        return fallback

    raise RuntimeError(
        f"Could not locate Fabric_4L repository root. "
        f"Set FABRIC_4L_ROOT or run from inside the repo."
    )


# ---------------------------------------------------------------------------
# Evidence / logging helpers (used by signoff_runner and similar)
# ---------------------------------------------------------------------------


def setup_evidence_dir(repo_root: Path, phase_name: str) -> Path:
    """Create and return the evidence directory for a named phase."""
    phase_dir = repo_root / "signoff-evidence" / phase_name
    phase_dir.mkdir(parents=True, exist_ok=True)
    return phase_dir


def log_evidence(path: Path, msg: str) -> None:
    """Append a single line to *path*, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(msg + "\n")


def log_and_print(path: Path, msg: str, out: TextIO = sys.stdout) -> None:
    """Append a line to *path* and echo it to *out*."""
    log_evidence(path, msg)
    out.write(msg + "\n")
