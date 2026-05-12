#!/usr/bin/env python3
"""Guard that value_fabric/layer5 remains compatibility shims only."""

from __future__ import annotations

from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    shim_root = root / "value_fabric" / "layer5"
    violations: list[str] = []

    for py_file in shim_root.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        if "from layer5_ground_truth" not in text:
            violations.append(str(py_file.relative_to(root)))

    if violations:
        print("ERROR: Layer 5 compatibility tree contains non-shim modules:")
        for v in violations:
            print(f" - {v}")
        return 1

    print("OK: Layer 5 compatibility tree is shim-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
