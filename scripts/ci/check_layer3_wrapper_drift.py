#!/usr/bin/env python3
"""Fail when service layer3 source diverges from canonical non-wrapper policy."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SERVICE_SRC = ROOT / "services/layer3-knowledge/src"
CANONICAL_SRC = ROOT / "value_fabric/layer3"


def _is_wrapper(text: str, module_path: str) -> bool:
    expected = f'"""Compatibility wrapper for {module_path}."""\n\nfrom {module_path} import *  # noqa: F401,F403\n'
    return text == expected


def main() -> int:
    violations: list[str] = []
    for service_file in sorted(SERVICE_SRC.rglob("*.py")):
        rel = service_file.relative_to(SERVICE_SRC)
        canonical_file = CANONICAL_SRC / rel
        if not canonical_file.exists():
            continue
        module_path = "value_fabric.layer3." + ".".join(rel.with_suffix("").parts)
        if any(part and part[0].isdigit() for part in rel.with_suffix("").parts):
            continue
        content = service_file.read_text(encoding="utf-8")
        if not _is_wrapper(content, module_path):
            violations.append(str(rel))

    if violations:
        print("Layer3 wrapper drift detected in services/layer3-knowledge/src:")
        for rel in violations:
            print(f" - {rel}")
        print("\nEach mirrored file must stay a thin wrapper to value_fabric.layer3.*")
        return 1

    print("Layer3 wrapper drift check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
