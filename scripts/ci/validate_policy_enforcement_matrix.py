#!/usr/bin/env python3
"""Fail if config/production-readiness files are missing matrix entries."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY_DIR = ROOT / "config" / "production-readiness"
MATRIX_PATH = ROOT / "docs" / "quality" / "policy-enforcement-matrix.md"
ROW_PATTERN = re.compile(r"\|\s*`(config/production-readiness/[^`]+)`\s*\|")


def main() -> int:
    if not MATRIX_PATH.exists():
        print(f"FAIL: missing matrix document: {MATRIX_PATH.relative_to(ROOT)}")
        return 1

    policy_files = {
        str(path.relative_to(ROOT))
        for path in sorted(POLICY_DIR.iterdir())
        if path.is_file()
    }
    matrix_entries = set(ROW_PATTERN.findall(MATRIX_PATH.read_text(encoding="utf-8")))

    missing_entries = sorted(policy_files - matrix_entries)
    stale_entries = sorted(matrix_entries - policy_files)

    if missing_entries:
        for entry in missing_entries:
            print(f"FAIL: policy file missing matrix entry: {entry}")
    if stale_entries:
        for entry in stale_entries:
            print(f"FAIL: matrix references non-existent policy file: {entry}")

    if missing_entries or stale_entries:
        return 1

    print(
        f"PASS: matrix covers all {len(policy_files)} production-readiness policy files"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
