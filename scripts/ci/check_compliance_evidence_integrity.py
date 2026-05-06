#!/usr/bin/env python3
"""Validate compliance evidence pointers are present and fresh."""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/reference/compliance.md"
SECTION_HEADER = "### Evidence Pointers Registry"
ROW_RE = re.compile(r"^\|\s*([^|]+)\|\s*([^|]+)\|\s*`([^`]+)`\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|$")
FREQ_RE = re.compile(r"(\d+)d")


@dataclass
class Pointer:
    control: str
    evidence_type: str
    path: str
    frequency: str
    max_age_days: int
    owner: str


def parse_registry() -> list[Pointer]:
    text = DOC.read_text(encoding="utf-8")
    if SECTION_HEADER not in text:
        raise ValueError(f"Missing section: {SECTION_HEADER}")
    section = text.split(SECTION_HEADER, 1)[1]
    lines = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    pointers: list[Pointer] = []
    for line in lines:
        if line.startswith("|---") or "Control Area" in line:
            continue
        m = ROW_RE.match(line)
        if not m:
            continue
        control, evidence_type, path, frequency, max_age_text, owner = [g.strip() for g in m.groups()]
        freq_match = FREQ_RE.search(max_age_text)
        if not freq_match:
            raise ValueError(f"Invalid max age format '{max_age_text}' for {path}; expected e.g. 30d")
        pointers.append(Pointer(control, evidence_type, path, frequency, int(freq_match.group(1)), owner))
    if not pointers:
        raise ValueError("No evidence pointers found")
    return pointers


def file_age_days(repo_path: str) -> int:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ct", "--", repo_path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return 10**9
    last_epoch = int(result.stdout.strip())
    then = datetime.fromtimestamp(last_epoch, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - then).days


def main() -> int:
    errors: list[str] = []
    pointers = parse_registry()
    for pointer in pointers:
        target = ROOT / pointer.path
        if not target.exists():
            errors.append(f"Missing evidence reference: {pointer.path} ({pointer.control})")
            continue
        age_days = file_age_days(pointer.path)
        if age_days > pointer.max_age_days:
            errors.append(
                f"Stale evidence reference: {pointer.path} is {age_days}d old (max {pointer.max_age_days}d)"
            )

    if errors:
        print("Compliance evidence integrity check failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print(f"Compliance evidence integrity check passed ({len(pointers)} pointers validated).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
