#!/usr/bin/env python3
"""Quick check: inspect Alembic revision graphs without running env.py."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SERVICES = {
    "layer1-ingestion": REPO_ROOT / "services" / "layer1-ingestion",
    "layer2-extraction": REPO_ROOT / "services" / "layer2-extraction",
    "layer4-agents": REPO_ROOT / "services" / "layer4-agents",
    "layer5-ground-truth": REPO_ROOT / "services" / "layer5-ground-truth",
}


def _find_versions_dir(service_dir: Path) -> Path | None:
    candidates = [
        service_dir / "migrations" / "versions",
        service_dir / "src" / "layer5_ground_truth" / "migrations" / "versions",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _extract_revisions(versions_dir: Path) -> dict[str, dict]:
    _REV_RE = re.compile(r'^revision\s*[:=]\s*["\']([^"\']+)["\']')
    _DOWN_RE = re.compile(r'^down_revision\s*[:=]\s*["\']?([^"\'#\s]+)["\']?')

    revisions: dict[str, dict] = {}
    for f in sorted(versions_dir.glob("*.py")):
        if f.name.startswith(("__", ".")):
            continue
        source = f.read_text(encoding="utf-8", errors="ignore")
        rev: str | None = None
        down_rev: str | None = None
        for line in source.splitlines():
            line = line.strip()
            if m := _REV_RE.match(line):
                rev = m.group(1)
            if m := _DOWN_RE.match(line):
                val = m.group(1)
                down_rev = None if val.lower() == "none" else val
        if rev:
            revisions[rev] = {"file": f.name, "down_revision": down_rev}
    return revisions


def main() -> int:
    errors = []
    warnings = []

    for name, service_dir in SERVICES.items():
        versions_dir = _find_versions_dir(service_dir)
        if not versions_dir:
            errors.append(f"{name}: no versions directory found")
            continue

        revisions = _extract_revisions(versions_dir)
        if not revisions:
            warnings.append(f"{name}: no migration revisions found")
            continue

        # Build reverse map: child -> parent
        children: dict[str, list[str]] = {}
        for rev, info in revisions.items():
            down = info["down_revision"]
            if down:
                children.setdefault(down, []).append(rev)

        # Find heads (revisions with no children)
        heads = [rev for rev in revisions if rev not in children]

        # Find roots (revisions with no down_revision)
        roots = [rev for rev, info in revisions.items() if info["down_revision"] is None]

        print(f"\n{name}: {len(revisions)} revisions, {len(heads)} head(s), {len(roots)} root(s)")
        for rev in heads:
            print(f"  HEAD: {rev} ({revisions[rev]['file']})")
        for rev in roots:
            print(f"  ROOT: {rev} ({revisions[rev]['file']})")

        if len(heads) > 1:
            errors.append(f"{name}: MULTI-HEAD detected ({len(heads)} heads: {heads})")

        # Check for duplicate revision IDs
        seen_files: dict[str, list[str]] = {}
        for rev, info in revisions.items():
            seen_files.setdefault(rev, []).append(info["file"])
        for rev, files in seen_files.items():
            if len(files) > 1:
                errors.append(f"{name}: DUPLICATE revision ID '{rev}' in files: {files}")

    if warnings:
        print("\n⚠️  Warnings:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("\n❌ Errors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\n✅ All Alembic revision graphs are clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
