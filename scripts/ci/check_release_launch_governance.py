#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKLIST = ROOT / "docs/launch-checklists/platform-launch.md"
REQUIRED_ITEMS = (
    "Contributor onboarding links to the canonical platform contract in `docs/contract.md`",
    "PR template requires explicit confirmations for contract shape, tenant isolation, and compatibility shim impact",
    "Launch drift prevention approvals are documented in `docs/governance/launch-drift-prevention-sop.md`",
)


def main() -> int:
    if not CHECKLIST.exists():
        print(f"Missing checklist: {CHECKLIST.relative_to(ROOT)}")
        return 1

    content = CHECKLIST.read_text(encoding="utf-8")
    failures: list[str] = []
    for item in REQUIRED_ITEMS:
        checked_pattern = re.compile(rf"(?m)^- \[x\] {re.escape(item)}\s*$")
        unchecked_pattern = re.compile(rf"(?m)^- \[ \] {re.escape(item)}\s*$")
        if checked_pattern.search(content):
            continue
        if unchecked_pattern.search(content):
            failures.append(f"unchecked required governance item: {item}")
        else:
            failures.append(f"missing required governance item: {item}")

    if failures:
        print("ERROR: release launch governance checklist is incomplete:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Release launch governance checklist items are checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
