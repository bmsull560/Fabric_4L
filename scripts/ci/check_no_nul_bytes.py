#!/usr/bin/env python3
"""Fail if tracked source/config files contain NUL bytes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ALLOWED_SUFFIXES = {".py", ".ts", ".tsx", ".json", ".yaml"}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"], check=True, capture_output=True, text=True
    )
    files: list[Path] = []
    for line in result.stdout.splitlines():
        path = Path(line)
        if path.suffix in ALLOWED_SUFFIXES:
            files.append(path)
    return files


def main() -> int:
    offenders: list[str] = []
    for path in tracked_files():
        data = path.read_bytes()
        if b"\x00" in data:
            offenders.append(f"{path} (nul_count={data.count(b'\x00')})")

    if offenders:
        print("ERROR: NUL-byte guard failed: tracked files with embedded \\x00 detected:")
        for offender in offenders:
            print(f"  - {offender}")
        print("Remove NUL bytes before merging.")
        return 1

    print("OK: NUL-byte guard passed: no tracked .py/.ts/.tsx/.json/.yaml files contain \\x00 bytes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
