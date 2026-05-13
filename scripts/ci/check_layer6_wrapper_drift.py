#!/usr/bin/env python3
"""Fail when non-canonical Layer 6 wrappers contain implementation logic."""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
WRAPPER_ROOT = ROOT / "services" / "layer6-benchmarks" / "src"

IMPORT_RE = re.compile(
    r"^from\s+value_fabric\.layer6(?:\.[\w_]+)*\s+import\s+\*\s*(?:#.*)?$"
)


def _is_wrapper_only(text: str) -> bool:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith('"""') or line.startswith("'''"):
            continue
        lines.append(line)

    if not lines:
        return True
    return all(IMPORT_RE.match(line) for line in lines)


def main() -> int:
    if not WRAPPER_ROOT.exists():
        print("Layer6 wrapper drift check passed (no compatibility wrapper tree present).")
        return 0

    failures: list[str] = []
    for path in sorted(WRAPPER_ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if not _is_wrapper_only(path.read_text(encoding="utf-8")):
            failures.append(str(rel))

    if failures:
        print("Layer6 wrapper drift detected in services/layer6-benchmarks/src:")
        for rel in failures:
            print(f" - {rel}")
        print("\nEach non-canonical file must remain a thin wrapper importing from value_fabric.layer6.*")
        return 1

    print("Layer6 wrapper drift check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
