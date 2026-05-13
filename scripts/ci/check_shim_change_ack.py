#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ci.compatibility_registry import parse_registry

REGISTRY = ROOT / "docs/governance/compatibility-debt-registry.md"
REQUIRED_LABELS = {"compat-shim-change", "compat-owner-ack"}


def shim_paths() -> set[str]:
    return {entry.normalized_path for entry in parse_registry(REGISTRY)}


def main() -> int:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        print("GITHUB_EVENT_PATH not set; skipping shim change ack check.")
        return 0

    payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
    pr = payload.get("pull_request") or {}
    changed = set(pr.get("changed_files_list", []))
    if not changed:
        # fallback for workflows that pass changed files via env var
        env_changed = os.environ.get("CHANGED_FILES", "")
        changed = {x.strip() for x in env_changed.split() if x.strip()}

    shim_set = shim_paths()
    touched = sorted(
        f for f in changed if any(f == s or f.startswith(s + "/") for s in shim_set)
    )
    if not touched:
        print("No compatibility shim path changes detected.")
        return 0

    labels = {item.get("name", "") for item in pr.get("labels", [])}
    missing = sorted(REQUIRED_LABELS - labels)
    if missing:
        print("ERROR: Compatibility shim files were changed but required labels are missing:")
        for m in missing:
            print(f"- {m}")
        print("Touched shim paths:")
        for path in touched:
            print(f"- {path}")
        return 1

    print("Compatibility shim changes acknowledged with required labels.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
