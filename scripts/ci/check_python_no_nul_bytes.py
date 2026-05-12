#!/usr/bin/env python3
"""Fail if tracked Python files contain NUL bytes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path



def tracked_python_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "*.py"], check=True, capture_output=True, text=True
    )
    return [Path(line) for line in result.stdout.splitlines() if line]



def main() -> int:
    offenders: list[str] = []
    for path in tracked_python_files():
        data = path.read_bytes()
        nul_count = data.count(b"\x00")
        if nul_count:
            offenders.append(f"{path} (nul_count={nul_count})")

    if offenders:
        print("ERROR: Python NUL-byte guard failed: tracked *.py files with embedded \\x00 detected:")
        for offender in offenders:
            print(f"  - {offender}")
        print("Remove NUL bytes before merging.")
        return 1

    print("OK: Python NUL-byte guard passed: no tracked *.py files contain \\x00 bytes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
