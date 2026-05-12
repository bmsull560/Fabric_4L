#!/usr/bin/env python3
"""Resolve git merge conflicts by keeping the 'ours' side (top half)."""
import sys
from pathlib import Path

def resolve_conflicts(filepath: str, keep: str = "ours") -> bool:
    """Strip conflict markers from a file, keeping chosen side."""
    p = Path(filepath)
    content = p.read_text(encoding="utf-8", errors="replace")
    if "<<<<<<<" not in content:
        print(f"  No conflicts in {filepath}")
        return False

    lines = content.splitlines(keepends=True)
    result = []
    in_conflict = False
    in_ours = True  # True when between <<<<<<< and =======

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("<<<<<<< "):
            in_conflict = True
            in_ours = True
            continue
        elif stripped.startswith("======="):
            in_ours = False
            continue
        elif stripped.startswith(">>>>>>> "):
            in_conflict = False
            in_ours = True
            continue

        if in_conflict:
            if keep == "ours" and in_ours:
                result.append(line)
            elif keep == "theirs" and not in_ours:
                result.append(line)
        else:
            result.append(line)

    p.write_text("".join(result), encoding="utf-8")
    print(f"  Resolved conflicts in {filepath}")
    return True

files = [
    "services/layer3-knowledge/README.md",
    ".github/workflows/supply-chain.yml",
    ".github/workflows/environment-promotion.yml",
    ".github/workflows/branch-protection-validation.yml",
    ".github/workflows/build-deploy.yml",
    "docs/reference/layer3-layer6-wrapper-policy.md",
    "scripts/ci/check_layer3_wrapper_drift.py",
    "reports/RELEASE_READINESS_AUDIT_2026-05-12.md",
]

changed = 0
for f in files:
    path = Path(f"c:/Users/BBB/Fabric_4L/{f}")
    if path.exists():
        if resolve_conflicts(str(path)):
            changed += 1
    else:
        print(f"  MISSING: {f}")

print(f"\nResolved conflicts in {changed} files.")
