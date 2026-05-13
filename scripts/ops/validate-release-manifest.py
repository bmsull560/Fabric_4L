#!/usr/bin/env python3
"""Validate canonical release artifacts before manifest signing."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def main() -> int:
    artifact_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts/release")
    gate_result = artifact_dir / "gate-result.json"
    summary = artifact_dir / "summary.md"

    missing = [str(path) for path in (gate_result, summary) if not path.is_file()]
    if missing:
        print(f"Missing required release artifacts: {', '.join(missing)}", file=sys.stderr)
        return 1

    gate_data = json.loads(gate_result.read_text(encoding="utf-8"))
    gate_sha = str(gate_data.get("git_sha") or "").strip()
    if not gate_sha:
        print("gate-result.json is missing git_sha", file=sys.stderr)
        return 1

    summary_text = summary.read_text(encoding="utf-8")
    match = re.search(r"\| Git SHA\s+\|\s+`([^`]+)`", summary_text)
    if not match:
        print("summary.md is missing Git SHA row", file=sys.stderr)
        return 1

    summary_sha = match.group(1).strip()
    if summary_sha != gate_sha:
        print(
            f"Release artifact SHA mismatch: gate-result.json={gate_sha} summary.md={summary_sha}",
            file=sys.stderr,
        )
        return 1

    print(f"Validated release manifest inputs for SHA {gate_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
