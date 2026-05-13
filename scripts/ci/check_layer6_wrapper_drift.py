#!/usr/bin/env python3
"""Fail when non-canonical Layer 6 wrappers drift from approved re-export shims."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
WRAPPER_ROOT = ROOT / "services" / "layer6-benchmarks" / "src"
MANIFEST = ROOT / "scripts" / "mirrored_files.json"

DOCSTRING_RE = re.compile(r'^"""Compatibility wrapper for (?P<module>value_fabric\.layer6(?:\.[\w_]+)*)\."""$')
IMPORT_RE = re.compile(
    r"^from\s+(?P<module>value_fabric\.layer6(?:\.[\w_]+)*)\s+import\s+\*\s*$"
)


def _load_expected_wrappers() -> dict[str, str]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    wrappers = data.get("wrapper_files", [])
    return {item["path"]: item["module"] for item in wrappers}


def _wrapper_module(text: str) -> str | None:
    lines = [raw.strip() for raw in text.splitlines() if raw.strip()]
    if len(lines) != 2:
        return None

    doc = DOCSTRING_RE.match(lines[0])
    imp = IMPORT_RE.match(lines[1])
    if doc is None or imp is None:
        return None
    if doc.group("module") != imp.group("module"):
        return None
    return imp.group("module")


def main() -> int:
    if not WRAPPER_ROOT.exists():
        print(f"Missing required Layer6 compatibility wrapper tree: {WRAPPER_ROOT}")
        return 1

    expected_wrappers = _load_expected_wrappers()
    failures: list[str] = []
    for path in sorted(WRAPPER_ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        rel_text = rel.as_posix()
        expected_module = expected_wrappers.get(rel_text)
        if expected_module is None:
            failures.append(f"{rel_text}: missing manifest entry")
            continue

        actual_module = _wrapper_module(path.read_text(encoding="utf-8"))
        if actual_module is None:
            failures.append(f"{rel_text}: file contains non-wrapper logic")
            continue
        if actual_module != expected_module:
            failures.append(
                f"{rel_text}: wrapper target mismatch "
                f"(expected {expected_module}, found {actual_module})"
            )

    actual_wrapper_paths = {
        path.relative_to(ROOT).as_posix() for path in WRAPPER_ROOT.rglob("*.py")
    }
    missing_files = sorted(set(expected_wrappers) - actual_wrapper_paths)
    for missing in missing_files:
        failures.append(f"{missing}: declared in manifest but file is missing")

    if failures:
        print("Layer6 wrapper drift detected in services/layer6-benchmarks/src:")
        for rel in failures:
            print(f" - {rel}")
        print(
            "\nEach non-canonical file must remain a manifest-backed thin wrapper "
            "importing from value_fabric.layer6.*"
        )
        return 1

    print("Layer6 wrapper drift check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
