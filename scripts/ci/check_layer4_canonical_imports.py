#!/usr/bin/env python3
"""Fail when non-canonical ``layer4_agents`` imports are introduced."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = [REPO_ROOT / "services", REPO_ROOT / "value_fabric", REPO_ROOT / "tests", REPO_ROOT / "scripts"]
PY_FILES = ("*.py",)
ALLOWED_FILES = {
    Path("layer4_agents/__init__.py"),
    Path("layer4_agents/main.py"),
    Path("tests/contract/test_import_topology.py"),
}
PATTERN = re.compile(r"(^|\s)(from|import)\s+layer4_agents(\.|\s|$)")


def main() -> int:
    violations: list[str] = []
    for root in SCAN_ROOTS:
        for pat in PY_FILES:
            for path in root.rglob(pat):
                rel = path.relative_to(REPO_ROOT)
                if rel in ALLOWED_FILES:
                    continue
                
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                for i, line in enumerate(text.splitlines(), start=1):
                    if PATTERN.search(line):
                        violations.append(f"{rel}:{i}: {line.strip()}")

    if violations:
        print("Layer 4 canonical import check failed. Use 'value_fabric.layer4' instead of 'layer4_agents'.", file=sys.stderr)
        for item in violations:
            print(f"  - {item}", file=sys.stderr)
        return 1

    print("OK: no non-canonical 'layer4_agents' imports found in scanned roots.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
