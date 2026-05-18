#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PyYAML is required to parse the skip register") from exc


def _load_entries(register_path: Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(register_path.read_text(encoding="utf-8")) if register_path.exists() else {}
    if not isinstance(raw, dict):
        return []
    entries = raw.get("entries", [])
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


def find_duplicates(register_path: Path) -> dict[tuple[str, str, str], list[tuple[int, str]]]:
    duplicates: dict[tuple[str, str, str], list[tuple[int, str]]] = defaultdict(list)
    for index, entry in enumerate(_load_entries(register_path), start=1):
        path_pattern = str(entry.get("path_pattern", "")).strip()
        marker = str(entry.get("marker", "")).strip()
        reason_pattern = str(entry.get("reason_pattern", "")).strip()
        key = (path_pattern, marker, reason_pattern)
        entry_id = str(entry.get("id", "<missing-id>")).strip() or "<empty-id>"
        duplicates[key].append((index, entry_id))
    return {key: rows for key, rows in duplicates.items() if len(rows) > 1}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Ensure config/ci/test_skip_register.yaml entries are unique by "
            "path_pattern + marker + reason_pattern"
        )
    )
    parser.add_argument("--register", type=Path, default=Path("config/ci/test_skip_register.yaml"))
    args = parser.parse_args()

    duplicates = find_duplicates(args.register)
    if not duplicates:
        print(f"PASS: no duplicate skip-register uniqueness keys found in {args.register.as_posix()}")
        return 0

    print(
        "FAIL: duplicate skip-register uniqueness keys found "
        f"in {args.register.as_posix()}\n"
        "Resolve by keeping one entry per (path_pattern, marker, reason_pattern) key."
    )
    for path_pattern, marker, reason_pattern in sorted(duplicates):
        print("\nDuplicate key:")
        print(f"  path_pattern: {path_pattern}")
        print(f"  marker: {marker}")
        print(f"  reason_pattern: {reason_pattern}")
        print("  Entries:")
        for line_number, entry_id in duplicates[(path_pattern, marker, reason_pattern)]:
            print(
                f"    - id={entry_id} at {args.register.as_posix()}:entries[{line_number}]"
            )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
