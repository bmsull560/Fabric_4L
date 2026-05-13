#!/usr/bin/env python3
"""Fail when configured mirrored files or wrapper templates diverge."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "mirrored_files.json"


def render_wrapper(module: str) -> bytes:
    text = f'"""Compatibility wrapper for {module}."""\n\nfrom {module} import *\n'
    return text.encode("utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pairs = data.get("mirrored_pairs", [])
    wrappers = data.get("wrapper_files", [])
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

    for wrapper in wrappers:
        path = ROOT / wrapper["path"]
        module = wrapper["module"]
        label = wrapper.get("name", wrapper["path"])

        if not path.exists():
            failures.append(f"{label}: missing wrapper file")
            continue

        expected = render_wrapper(module)
        actual = path.read_bytes()
        if actual != expected:
            failures.append(
                f"{label}: wrapper content mismatch\n"
                f"  path={wrapper['path']}\n"
                f"  expected_module={module}"
            )

    if failures:
        print("Mirror or wrapper drift detected:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        "Mirror check passed for "
        f"{len(pairs)} mirrored pair(s) and {len(wrappers)} wrapper file(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
