#!/usr/bin/env python3
"""Fail closed if the backend workflow traceability matrix loses release-significant lineage markers."""

from __future__ import annotations

import sys
from pathlib import Path


MATRIX_PATH = Path("docs/contracts/workflow-traceability-matrix.md")

REQUIRED_WORKFLOWS = [
    "## Workflow 1: Configure Ingestion → Run Ingestion → Monitor Job",
    "## Workflow 2: Trigger Extraction → Monitor Extraction → Retrieve Results",
    "## Workflow 3: Persist to Graph → Query Entities / Subgraph",
    "## Workflow 4: Build Value Tree → Attach Formulas / Models / Variables",
    "## Workflow 5: Run Agent Workflow → Monitor via SSE → Complete / Fail",
    "## Workflow 6: Validate Output Against Ground Truth → View Benchmarks",
    "## Workflow 7: Export Document / Business Case",
    "## Workflow 8: Submit for Review → Approve / Reject → Trace Version History",
    "## Workflow 9: Search and Retrieval → Open Result in Correct Context",
    "## Workflow 10: Convert Value Case → Track Realized Outcomes",
]

REQUIRED_MARKERS = {
    "document purpose": "> Map every user-facing workflow step to backend objects, status fields, and event sources.",
    "matrix contract section": "## Matrix Maintenance Contract",
    "frontend matrix cross-link": "`docs/validation/master_workflow_traceability_matrix.md`",
    "frontend subset cross-link": "`apps/web/docs/frontend-workflow-coverage-matrix.md`",
    "root guard command": "`python3 scripts/ci/assert_backend_workflow_traceability.py`",
    "root make target": "`make check-workflow-matrix`",
    "extraction results gap": "QK.extraction.results(id)",
    "approval lineage gap": "immutable approval history, version comparison, and audit export",
    "search lineage gap": "canonical search result envelope",
    "realization linkage gap": "stable `plan_id` to `case_id` linkage",
    "event source summary": "## Event Source Summary",
    "id propagation chain": "## ID Propagation Chain",
    "trace recommendation": "trace_id` or `session_id`",
}


def main() -> int:
    if not MATRIX_PATH.exists():
        print(f"Missing backend workflow traceability matrix: {MATRIX_PATH}", file=sys.stderr)
        return 1

    matrix = MATRIX_PATH.read_text(encoding="utf-8")
    failures: list[str] = []

    for heading in REQUIRED_WORKFLOWS:
        if heading not in matrix:
            failures.append(f"Missing workflow section: {heading}")

    for label, marker in REQUIRED_MARKERS.items():
        if marker not in matrix:
            failures.append(f"Missing {label}: {marker}")

    if failures:
        print(f"Backend workflow traceability matrix is incomplete: {MATRIX_PATH}", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1

    print(
        "Backend workflow traceability matrix passed: "
        f"{len(REQUIRED_WORKFLOWS)} workflow sections and {len(REQUIRED_MARKERS)} lineage markers present."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())