#!/usr/bin/env python3
"""Generate PR-diff scoped violation summary artifacts.

Compares strict CI violation reports against files changed in the PR diff
(base...HEAD) and writes JSON + Markdown summaries.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def _changed_files(base_ref: str) -> set[str]:
    cmd = ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--duplicate-report", type=Path, required=True)
    parser.add_argument("--shared-report", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--md-out", type=Path, required=True)
    args = parser.parse_args()

    changed = _changed_files(args.base_ref)
    dup = _load_json(args.duplicate_report)
    shared = _load_json(args.shared_report)

    duplicate_hits = []
    for v in dup.get("violations", []):
        vf = v.get("value_fabric", "")
        svc = v.get("service", "")
        if vf in changed or svc in changed:
            duplicate_hits.append(v)

    shared_hits = [f for f in shared.get("findings", []) if f.get("path", "") in changed]

    summary = {
        "base_ref": args.base_ref,
        "changed_files_count": len(changed),
        "new_duplicate_source_tree_violations": duplicate_hits,
        "new_shared_import_runtime_violations": shared_hits,
        "new_violation_count": len(duplicate_hits) + len(shared_hits),
    }

    args.json_out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# CI Violation Diff Summary",
        "",
        f"- Base ref: `origin/{args.base_ref}`",
        f"- Changed files: `{len(changed)}`",
        f"- Newly introduced violations in diff: `{summary['new_violation_count']}`",
        "",
        "## Duplicate source-tree violations (diff-scoped)",
    ]
    if duplicate_hits:
        md_lines += [f"- `{v['value_fabric']}` vs `{v['service']}`" for v in duplicate_hits]
    else:
        md_lines.append("- None")

    md_lines += ["", "## Shared import runtime violations (diff-scoped)"]
    if shared_hits:
        md_lines += [f"- `{f['path']}:{f['line']}` — `{f['import_statement']}`" for f in shared_hits]
    else:
        md_lines.append("- None")

    args.md_out.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
