#!/usr/bin/env python3
"""Fail CI when Layer 3 service-local files violate governance contracts.

Architecture note (ADR-027, accepted 2026-05-13):
  value_fabric/layer3/__init__.py is a path-redirect shim that appends
  services/layer3-knowledge/src/ to __path__.  This makes
  services/layer3-knowledge/src/ the canonical source tree — it is NOT a
  compatibility mirror of value_fabric/layer3/.  Mirror-parity checks between
  the two trees are therefore architecturally invalid and have been removed.

This script enforces two remaining contracts:
  1. Files in EXCEPTION_DIRS must carry a governance docstring (owner + target).
  2. No file in the service tree may contain unresolved merge-conflict markers.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPAT_ROOT = ROOT / "services" / "layer3-knowledge" / "src"

# Directories whose files require an explicit governance docstring because they
# contain service-local logic that is not part of the shared canonical runtime.
EXCEPTION_DIRS = ("api", "agents", "cache", "docs", "metrics", "migrations")
EXCEPTION_FILES = ("config.py",)
EXCEPTION_OWNER = "Owner: layer3-knowledge"
EXCEPTION_TARGET = "Removal/migration target: 2026-09-30"


def _py_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _is_exception_path(rel: Path) -> bool:
    return rel.as_posix() in EXCEPTION_FILES or (rel.parts and rel.parts[0] in EXCEPTION_DIRS)


def _has_exception_docstring(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return False
    doc = ast.get_docstring(tree)
    if not doc:
        return False
    return "Allowed service-local exception" in doc and EXCEPTION_OWNER in doc and EXCEPTION_TARGET in doc


def _violations() -> list[str]:
    violations: list[str] = []
    compat_files = {path.relative_to(COMPAT_ROOT) for path in _py_files(COMPAT_ROOT)}

    # Contract 1: governance docstrings on exception-path files
    for rel in sorted(compat_files):
        if not _is_exception_path(rel):
            continue
        if not _has_exception_docstring(COMPAT_ROOT / rel):
            violations.append(
                "service-local exception missing required governance docstring: "
                f"services/layer3-knowledge/src/{rel.as_posix()}"
            )

    # Contract 2: no unresolved merge-conflict markers anywhere in the service tree.
    # Match the full three-marker pattern to avoid false positives from section
    # dividers that use repeated '=' characters in comments.
    for rel in sorted(compat_files):
        path = COMPAT_ROOT / rel
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        # A real conflict block starts with "<<<<<<< " (7 < followed by a space
        # or branch name) and ends with ">>>>>>> " — check for both anchors.
        if "<<<<<<<" in text and ">>>>>>>" in text:
            violations.append(
                "merge conflict markers detected: "
                f"services/layer3-knowledge/src/{rel.as_posix()}"
            )

    return violations


def main() -> int:
    violations = _violations()
    if not violations:
        print("OK: Layer 3 canonical tree and compatibility shims are aligned.")
        return 0

    print("ERROR: Layer 3 source-of-truth contract failed.")
    print("Canonical source-of-truth: value_fabric/layer3")
    print("Compatibility shims: services/layer3-knowledge/src (mirrored paths only)")
    for violation in violations:
        print(f" - {violation}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
