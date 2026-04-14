#!/usr/bin/env python3
"""Generate release evidence artifacts for billing/entitlement regression checks."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET


def _parse_junit(xml_path: Path) -> dict[str, int]:
    root = ET.parse(xml_path).getroot()

    tests = int(root.attrib.get("tests", 0))
    failures = int(root.attrib.get("failures", 0))
    errors = int(root.attrib.get("errors", 0))
    skipped = int(root.attrib.get("skipped", 0))

    # Some pytest junitxml structures put totals on nested testsuite.
    if tests == 0 and root.tag == "testsuites":
        for suite in root.findall("testsuite"):
            tests += int(suite.attrib.get("tests", 0))
            failures += int(suite.attrib.get("failures", 0))
            errors += int(suite.attrib.get("errors", 0))
            skipped += int(suite.attrib.get("skipped", 0))

    return {
        "tests": tests,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "passed": max(0, tests - failures - errors - skipped),
    }


def _build_markdown(summary: dict[str, object]) -> str:
    generated_at = summary["generated_at_utc"]
    status = summary["status"]
    counts = summary["counts"]
    command = summary["test_command"]

    return "\n".join(
        [
            "# Billing & Entitlement Regression Evidence",
            "",
            "## Release Checklist Signal",
            f"- **Status:** `{status}`",
            f"- **Generated (UTC):** `{generated_at}`",
            f"- **Commit:** `{summary['git_sha']}`",
            f"- **Workflow run id:** `{summary['github_run_id']}`",
            "",
            "## Test Summary",
            f"- Total: **{counts['tests']}**",
            f"- Passed: **{counts['passed']}**",
            f"- Failed: **{counts['failures']}**",
            f"- Errors: **{counts['errors']}**",
            f"- Skipped: **{counts['skipped']}**",
            "",
            "## Executed Command",
            f"```bash\n{command}\n```",
            "",
            "## Scope",
            "- Plan/entitlement enforcement per tenant and region",
            "- Feature-flag interaction with entitlement limits",
            "- Billing-impacting scenarios (upgrade/downgrade, metering, overage)",
            "- Contract checks for billing/entitlement APIs when exposed",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--junit", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--test-command", required=True)
    args = parser.parse_args()

    counts = _parse_junit(args.junit)
    status = "pass" if counts["failures"] == 0 and counts["errors"] == 0 else "fail"

    summary = {
        "artifact_type": "billing_entitlements_regression_summary",
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "git_sha": os.getenv("GITHUB_SHA", "local"),
        "github_run_id": os.getenv("GITHUB_RUN_ID", "local"),
        "test_command": args.test_command,
        "counts": counts,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "billing-entitlements-summary.json"
    md_path = args.out_dir / "billing-entitlements-summary.md"

    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_build_markdown(summary), encoding="utf-8")


if __name__ == "__main__":
    main()
