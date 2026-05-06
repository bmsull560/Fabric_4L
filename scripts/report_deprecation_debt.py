#!/usr/bin/env python3
"""Scan repository for legacy/deprecated surface markers and report debt counts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class Rule:
    key: str
    pattern: str
    description: str


RULES: List[Rule] = [
    Rule("legacy_prefix", r"\blegacy_[A-Za-z0-9_]*", "Identifiers using legacy_ prefix"),
    Rule("deprecated_tag", r"@deprecated", "Explicit @deprecated tags"),
    Rule("alias_router_registration", r"\b(alias_router|legacy_router|register_alias_route|add_alias_route)\b", "Known alias router registrations"),
]

DEFAULT_GLOBS = ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.md", "*.yml", "*.yaml"]
EXCLUDE_GLOBS = [".git", "node_modules", "dist", "build", ".venv", "venv", "coverage", "__pycache__"]


def run_rg(pattern: str, globs: List[str]) -> int:
    cmd = ["rg", "-n", "--hidden", "--no-messages", "--glob", "!.git"]
    for ex in EXCLUDE_GLOBS:
        cmd.extend(["--glob", f"!{ex}/**"])
    for g in globs:
        cmd.extend(["--glob", g])
    cmd.extend(["-e", pattern, "."])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode not in (0, 1):
        print(proc.stderr, file=sys.stderr)
        raise RuntimeError(f"rg failed for pattern: {pattern}")
    if not proc.stdout.strip():
        return 0
    return len(proc.stdout.strip().splitlines())


def load_thresholds(path: Path | None) -> Dict[str, int]:
    if not path:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    thresholds = data.get("thresholds", {})
    return {k: int(v) for k, v in thresholds.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["warn", "enforce"], default="warn")
    parser.add_argument("--thresholds", type=Path, help="JSON file with thresholds object")
    parser.add_argument("--output", type=Path, default=Path("deprecation-debt-report.json"))
    parser.add_argument("--globs", nargs="*", default=DEFAULT_GLOBS)
    args = parser.parse_args()

    thresholds = load_thresholds(args.thresholds)
    counts: Dict[str, int] = {}
    violations: List[dict] = []

    for rule in RULES:
        count = run_rg(rule.pattern, args.globs)
        counts[rule.key] = count
        limit = thresholds.get(rule.key)
        if args.mode == "enforce" and limit is not None and count > limit:
            violations.append({"rule": rule.key, "count": count, "threshold": limit})

    report = {
        "mode": args.mode,
        "counts": counts,
        "thresholds": thresholds,
        "violations": violations,
        "status": "fail" if violations else "ok",
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("Deprecation debt scan complete")
    for key, count in counts.items():
        print(f"- {key}: {count}")

    if args.mode == "enforce" and violations:
        print("Blocking threshold violations:")
        for v in violations:
            print(f"  - {v['rule']}: {v['count']} > {v['threshold']}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
