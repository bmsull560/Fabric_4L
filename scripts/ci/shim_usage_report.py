#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ci.compatibility_registry import parse_registry

REGISTRY = ROOT / "docs/governance/compatibility-debt-registry.md"


def rg_count(pattern: str) -> int:
    cmd = ["rg", "--fixed-strings", "--glob", "*.py", "--glob", "*.ts", "--glob", "*.tsx", "--glob", "*.md", "--glob", "*.yml", "--glob", "*.yaml", "--glob", "*.json", "--count", pattern, str(ROOT)]
    out = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if out.returncode not in (0, 1):
        raise RuntimeError(out.stderr.strip() or "rg failed")
    total = 0
    for line in out.stdout.splitlines():
        try:
            total += int(line.rsplit(":", 1)[1])
        except Exception:
            continue
    return total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(ROOT / "artifacts" / "compatibility-debt"))
    args = parser.parse_args()
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []
    today = dt.date.today().isoformat()
    for shim in parse_registry(REGISTRY):
        count = max(0, rg_count(shim.path) - 1)  # subtract registry self-reference
        rows.append({
            "date": today,
            "shim_id": shim.shim_id,
            "path": shim.path,
            "owner": shim.owner,
            "target_removal_date": shim.target_removal_date,
            "remaining_callsites": count,
        })

    (outdir / "shim-usage-latest.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    with (outdir / "shim-usage-latest.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["date", "shim_id", "path", "owner", "target_removal_date", "remaining_callsites"])
        writer.writeheader()
        writer.writerows(rows)

    month = dt.date.today().replace(day=1).isoformat()
    md = [f"# Monthly compatibility shim report ({month})", "", "| ID | Remaining shim callsites | Path |", "|---|---:|---|"]
    for row in rows:
        md.append(f"| {row['shim_id']} | {row['remaining_callsites']} | `{row['path']}` |")
    (outdir / "monthly-shim-report.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("Generated shim usage report:")
    for row in rows:
        print(f"- {row['shim_id']}: {row['remaining_callsites']} callsites")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
