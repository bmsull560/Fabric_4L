#!/usr/bin/env python3
"""Summarize temporary compatibility tests so debt burn-down stays visible in CI."""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
TEST_ROOTS = [ROOT / "tests", ROOT / "services"]
TMP_MARKER = re.compile(r"@pytest\.mark\.temporary_compat")
TMP_NAME = re.compile(r"def\s+test_temp_compat__")


def iter_test_files() -> list[Path]:
    files: list[Path] = []
    for root in TEST_ROOTS:
        if not root.exists():
            continue
        files.extend(p for p in root.rglob("test_*.py") if p.is_file())
    return sorted(files)


def main() -> int:
    by_file: dict[str, int] = {}
    marker_total = 0
    naming_total = 0

    for path in iter_test_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        marker_count = len(TMP_MARKER.findall(text))
        naming_count = len(TMP_NAME.findall(text))
        total = marker_count + naming_count
        if total:
            rel = path.relative_to(ROOT).as_posix()
            by_file[rel] = total
            marker_total += marker_count
            naming_total += naming_count

    grand_total = marker_total + naming_total
    print("=== Compatibility Debt Summary ===")
    print(f"Temporary compatibility tests: {grand_total}")
    print(f"  via marker (@pytest.mark.temporary_compat): {marker_total}")
    print(f"  via naming (test_temp_compat__*): {naming_total}")
    if by_file:
        print("\nBreakdown by file:")
        for rel, count in by_file.items():
            print(f"- {rel}: {count}")
    else:
        print("\nNo temporary compatibility tests found.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
