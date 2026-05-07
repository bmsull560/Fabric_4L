#!/usr/bin/env python3
"""Govern pytest skip reasons captured during collection.

- Parses pytest output (typically from `pytest --collect-only -rs -q`).
- Allows infrastructure/environment skips by default pattern.
- Flags code-health skips as policy violations unless temporarily allowlisted.
- Tracks skip-count regressions via a baseline file.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

SKIP_LINE_RE = re.compile(r"^SKIPPED\s+\[(\d+)\]\s+(.+?)\s*$")

ALLOWED_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(redis|postgres|mysql|db|database|neo4j|kafka|rabbitmq)\b",
        r"\b(k8s|kubernetes|kubectl|helm|kind|minikube|cluster)\b",
        r"\b(docker|container|service unavailable|external service)\b",
        r"\b(environment|env var|missing secret|credentials)\b",
    ]
]

DENIED_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"import path unresolved",
        r"module not found",
        r"modulenotfounderror",
        r"importerror",
        r"pending refactor",
        r"todo",
        r"temporary skip",
    ]
]


@dataclass
class SkipRecord:
    count: int
    reason: str


def parse_skips(text: str) -> list[SkipRecord]:
    out: list[SkipRecord] = []
    for line in text.splitlines():
        m = SKIP_LINE_RE.match(line.strip())
        if not m:
            continue
        out.append(SkipRecord(count=int(m.group(1)), reason=m.group(2)))
    return out


def is_allowed(reason: str) -> bool:
    return any(p.search(reason) for p in ALLOWED_PATTERNS)


def is_denied(reason: str) -> bool:
    return any(p.search(reason) for p in DENIED_PATTERNS)


def load_allowlist(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = data.get("entries", [])
    by_pattern: dict[str, dict[str, str]] = {}
    for e in entries:
        pattern = e.get("pattern")
        if pattern:
            by_pattern[pattern] = e
    return by_pattern


def matches_allowlist(reason: str, allowlist: dict[str, dict[str, str]]) -> tuple[bool, str | None]:
    today = date.today()
    for pattern, meta in allowlist.items():
        if re.search(pattern, reason, re.IGNORECASE):
            exp = meta.get("expires")
            if exp:
                y, m, d = map(int, exp.split("-"))
                if date(y, m, d) < today:
                    return False, f"allowlist entry expired on {exp} ({meta.get('owner', 'unknown owner')})"
            return True, None
    return False, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="pytest output file")
    ap.add_argument("--allowlist", default="scripts/ci/pytest_skip_allowlist.yaml")
    ap.add_argument("--baseline", default="scripts/ci/pytest_skip_baseline.json")
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args()

    text = Path(args.input).read_text(encoding="utf-8", errors="ignore")
    skips = parse_skips(text)
    total = sum(s.count for s in skips)
    collection_import_errors = len(re.findall(r"(ModuleNotFoundError|ImportError)", text, flags=re.IGNORECASE))

    allowlist = load_allowlist(Path(args.allowlist))
    violations: list[str] = []
    categorized: dict[str, int] = {"infra_allowed": 0, "code_health": 0, "other": 0}

    for s in skips:
        if is_denied(s.reason):
            ok, err = matches_allowlist(s.reason, allowlist)
            if ok:
                categorized["other"] += s.count
            else:
                categorized["code_health"] += s.count
                msg = f"{s.count}x {s.reason}"
                if err:
                    msg += f" ({err})"
                violations.append(msg)
            continue

        if is_allowed(s.reason):
            categorized["infra_allowed"] += s.count
        else:
            ok, err = matches_allowlist(s.reason, allowlist)
            if ok:
                categorized["other"] += s.count
            else:
                categorized["other"] += s.count

    baseline_path = Path(args.baseline)
    if args.write_baseline:
        baseline_path.write_text(json.dumps({"total_skips": total, "categorized": categorized}, indent=2) + "\n", encoding="utf-8")
        print(f"wrote skip baseline: {baseline_path}")
        return 0

    if collection_import_errors > 0:
        violations.append(f"collection import-path unresolved errors detected: {collection_import_errors}")

    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        prev_total = int(baseline.get("total_skips", 0))
        if total > prev_total:
            violations.append(f"skip regression: current={total} baseline={prev_total}")

    print(f"skip summary: total={total} infra_allowed={categorized['infra_allowed']} code_health={categorized['code_health']} other={categorized['other']}")
    if violations:
        print("policy violations:", file=sys.stderr)
        for v in violations:
            print(f"- {v}", file=sys.stderr)
        return 1

    print("skip governance check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
