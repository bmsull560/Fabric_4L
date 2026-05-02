#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
PROD_UI = REPO_ROOT / "apps/web/client/src/components/ui"
PROTOTYPE_UI = REPO_ROOT / "prototypes/ui-prototype/non-production/ui-components-archive"
BASELINE_FILE = REPO_ROOT / "scripts/ui_duplicate_baseline.txt"


def filenames(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {p.name for p in path.glob("*") if p.is_file()}


prod = filenames(PROD_UI)
proto = filenames(PROTOTYPE_UI)
current = sorted(prod & proto)
baseline = set()
if BASELINE_FILE.exists():
    baseline = {line.strip() for line in BASELINE_FILE.read_text().splitlines() if line.strip() and not line.startswith("#")}

new_duplicates = sorted(set(current) - baseline)
if new_duplicates:
    print("❌ New duplicate UI component filenames detected across prototype and production trees:")
    for name in new_duplicates:
        print(f"  - {name}")
    print("\nResolve by renaming/removing prototype files or migrating to canonical production path.")
    sys.exit(1)

print(f"✅ UI duplicate filename guard passed (baseline={len(baseline)}, current={len(current)}, new={len(new_duplicates)})")
