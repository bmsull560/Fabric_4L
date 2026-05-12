#!/usr/bin/env python3
"""Fail if root-level temp_*.ts files are introduced.

These files are typically scratch artifacts and should not live in runtime
locations at repository root.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    offenders = sorted(
        path.name
        for path in REPO_ROOT.glob("temp_*.ts")
        if path.is_file()
    )

    if offenders:
        print("Found disallowed root-level temp TypeScript files:")
        for offender in offenders:
            print(f" - {offender}")
        print("Move scratch/reference files into docs/archive/ or delete them.")
        return 1

    print("No root-level temp_*.ts runtime-like files found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
