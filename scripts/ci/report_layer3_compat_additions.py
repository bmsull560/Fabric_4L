#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs/governance/compatibility-debt-registry.md"
LAYER3_ROOTS = ("value_fabric/layer3/", "services/layer3-knowledge/src/")


def _registry_text() -> str:
    return REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""


def _changed_files() -> list[str]:
    raw = os.environ.get("CHANGED_FILES", "")
    return [x.strip() for x in raw.split() if x.strip()]


def _is_compat_path(path: str) -> bool:
    lower = path.lower()
    return lower.endswith(".py") and path.startswith(LAYER3_ROOTS) and ("compat" in lower or "legacy" in lower)


def main() -> int:
    registry = _registry_text()
    changed = _changed_files()
    flagged = [p for p in changed if _is_compat_path(p) and p not in registry]
    if not flagged:
        print("Layer3 compatibility additions check: no unregistered additions detected.")
        return 0

    print("Layer3 compatibility additions without registry entry detected:")
    for p in flagged:
        print(f"- {p}")
        print(f"::warning file={p}::New Layer3 compatibility path without compatibility registry entry")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
