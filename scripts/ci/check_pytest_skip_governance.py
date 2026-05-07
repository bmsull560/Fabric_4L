#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None

SKIP_LINE = re.compile(r"^SKIPPED\s+\[[0-9]+\].*?:\s*(?P<reason>.+)$")

INFRA_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bdb\b|database|postgres|mysql|sqlite",
        r"\bredis\b",
        r"\bk8s\b|kubernetes|kubectl|kustomize|helm",
        r"docker|container runtime",
        r"environment variable|missing env|requires? env",
        r"external service unavailable|service unavailable",
    ]
]

CODE_HEALTH_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"import path.*unresolved",
        r"module not found",
        r"cannot import",
        r"pending refactor",
        r"legacy import layout",
    ]
]


@dataclass
class AllowEntry:
    pattern: re.Pattern[str]
    owner: str
    expires_on: date
    note: str


def load_allowlist(path: Path) -> list[AllowEntry]:
    if not path.exists():
        return []
    if yaml is None:
        raise RuntimeError("pyyaml is required to parse allowlist")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = raw.get("allowlist", [])
    out: list[AllowEntry] = []
    for i, entry in enumerate(entries):
        pattern = entry.get("pattern")
        owner = entry.get("owner")
        expires = entry.get("expires_on")
        note = entry.get("note", "")
        if not pattern or not owner or not expires:
            raise ValueError(f"Invalid allowlist entry index {i}: pattern, owner, expires_on required")
        out.append(AllowEntry(re.compile(pattern, re.IGNORECASE), owner, date.fromisoformat(expires), note))
    return out


def classify_reason(reason: str, allowlist: list[AllowEntry], today: date) -> tuple[str, str]:
    for entry in allowlist:
        if entry.pattern.search(reason):
            if entry.expires_on < today:
                return ("violation", f"expired allowlist ({entry.owner}, expired {entry.expires_on.isoformat()})")
            return ("allowlisted", f"allowlisted by {entry.owner} until {entry.expires_on.isoformat()}")

    if any(p.search(reason) for p in CODE_HEALTH_PATTERNS):
        return ("violation", "code-health skip")
    if any(p.search(reason) for p in INFRA_PATTERNS):
        return ("allowed", "infrastructure/environment skip")
    return ("violation", "unclassified skip reason")


def main() -> int:
    ap = argparse.ArgumentParser(description="Govern pytest skip reasons from collection output")
    ap.add_argument("collection_output", type=Path)
    ap.add_argument("--allowlist", type=Path, default=Path("config/ci/pytest_skip_allowlist.yaml"))
    ap.add_argument("--baseline", type=Path, default=Path("config/ci/pytest_skip_baseline.json"))
    ap.add_argument("--write-report", type=Path)
    args = ap.parse_args()

    content = args.collection_output.read_text(encoding="utf-8")
    reasons = [m.group("reason").strip() for line in content.splitlines() if (m := SKIP_LINE.match(line.strip()))]

    allowlist = load_allowlist(args.allowlist)
    today = date.today()

    counts: dict[str, int] = {}
    classified: list[dict[str, str]] = []
    violations: list[dict[str, str]] = []

    for reason in reasons:
        counts[reason] = counts.get(reason, 0) + 1

    for reason, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        status, detail = classify_reason(reason, allowlist, today)
        row = {"reason": reason, "count": str(count), "status": status, "detail": detail}
        classified.append(row)
        if status == "violation":
            violations.append(row)

    baseline_total = None
    if args.baseline.exists():
        baseline_total = int(json.loads(args.baseline.read_text(encoding="utf-8")).get("max_total_skips", 0))

    total_skips = len(reasons)
    regression = baseline_total is not None and total_skips > baseline_total

    report = {
        "total_skips": total_skips,
        "baseline_max_total_skips": baseline_total,
        "regression": regression,
        "classified": classified,
        "violations": violations,
    }
    if args.write_report:
        args.write_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"total skipped entries: {total_skips}")
    for row in classified:
        print(f"- [{row['status']}] x{row['count']} :: {row['reason']} ({row['detail']})")

    if regression:
        print(
            f"ERROR: skip count regression detected (total {total_skips} > baseline {baseline_total}).",
            file=sys.stderr,
        )
    if violations:
        print("ERROR: policy-violating skip reasons detected:", file=sys.stderr)
        for v in violations:
            print(f"  - x{v['count']} {v['reason']} ({v['detail']})", file=sys.stderr)

    return 1 if regression or violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
