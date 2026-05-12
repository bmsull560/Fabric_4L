#!/usr/bin/env python3
"""Fail when configured mirrored file pairs diverge."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "mirrored_files.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pairs = data.get("mirrored_pairs", [])
    failures: list[str] = []

    for pair in pairs:
        canonical = ROOT / pair["canonical"]
        mirror = ROOT / pair["mirror"]
        label = pair.get("name", f"{canonical} == {mirror}")

        if not canonical.exists() or not mirror.exists():
            failures.append(f"{label}: missing file(s)")
            continue

        if sha256(canonical) != sha256(mirror):
            failures.append(
                f"{label}: hash mismatch\n"
                f"  canonical={pair['canonical']}\n"
                f"  mirror={pair['mirror']}"
            )

    if failures:
        print("Mirror drift detected:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Mirror check passed for {len(pairs)} pair(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
