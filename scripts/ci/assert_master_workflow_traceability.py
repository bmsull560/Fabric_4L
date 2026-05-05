#!/usr/bin/env python3
"""Fail closed if the master workflow traceability matrix loses release-significant coverage markers."""

from __future__ import annotations

import sys
from pathlib import Path


MATRIX_PATH = Path("docs/validation/master_workflow_traceability_matrix.md")

REQUIRED_WORKFLOW_ROWS = [
    "| 1 | Authentication, Tenant, and Workspace Access |",
    "| 2 | Account and Prospect Setup |",
    "| 3 | Data Ingestion Workflows — Layer 1 |",
    "| 4 | Extraction and Signal Detection — Layer 2 |",
    "| 5 | Knowledge Graph and Context Engine — Layer 3 |",
    "| 6 | Value Pack Selection and Governance |",
    "| 7 | Prospect Intelligence Workflow |",
    "| 8 | Stakeholder Mapping |",
    "| 9 | Hypothesis Generation Workflow — Layer 4 |",
    "| 10 | Value Driver Tree Workflow |",
    "| 11 | Evidence Matching Workflow |",
    "| 12 | Benchmark and Ground Truth Workflow — Layers 5 and 6 |",
    "| 13 | Formula Selection and Calculation Workflow |",
    "| 14 | Value Calculator Workflow |",
    "| 15 | Business Case Generation Workflow |",
    "| 16 | Narrative and Proposal Workflow |",
    "| 17 | Agentic Chat and Right-Rail Workflow |",
    "| 18 | Review, Approval, and Governance Workflow |",
    "| 19 | Versioning, Audit, and Traceability |",
    "| 20 | Collaboration Workflow |",
    "| 21 | CRM and External System Workflow |",
    "| 22 | Value Realization Workflow |",
    "| 23 | Search and Retrieval Workflow |",
    "| 24 | Notifications and Task Workflow |",
    "| 25 | Admin Configuration Workflow |",
    "| 26 | Security and Compliance User Workflows |",
    "| 27 | Error, Empty State, and Recovery Workflows |",
    "| 28 | Full End-to-End Golden Path |",
    "| 29 | Full End-to-End Adversarial Path |",
    "| 30 | Persona-Based Validation Journeys |",
]

REQUIRED_MARKERS = {
    "matrix contract section": "## Matrix Maintenance Contract",
    "executive matrix": "## Executive Master Traceability Matrix",
    "validation gate map": "## Validation Gate Map",
    "execution cadence": "## Execution Cadence",
    "gap prioritization": "## Gap Prioritization",
    "next implementation batch": "## Recommended Next Implementation Batch",
    "frontend validation baseline": "`pnpm run test:e2e:validation`",
    "frontend deep validation": "`pnpm run test:e2e:validation:p0:deep`",
    "frontend anti-skip guard": "`pnpm run test:e2e:guard`",
    "backend integrated make target": "`make test-backend-integrated-validation`",
    "release smoke make target": "`make test-backend-integrated-release-smoke`",
    "security gate reference": "`make security-smoke`",
    "contract traceability cross-link": "`docs/contracts/workflow-traceability-matrix.md`",
}


def main() -> int:
    if not MATRIX_PATH.exists():
        print(f"Missing master workflow matrix: {MATRIX_PATH}", file=sys.stderr)
        return 1

    matrix = MATRIX_PATH.read_text(encoding="utf-8")
    failures: list[str] = []

    for label, marker in REQUIRED_MARKERS.items():
        if marker not in matrix:
            failures.append(f"Missing {label}: {marker}")

    for row in REQUIRED_WORKFLOW_ROWS:
        if row not in matrix:
            failures.append(f"Missing workflow row: {row}")

    if failures:
        print(f"Master workflow matrix is incomplete: {MATRIX_PATH}", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1

    print(
        "Master workflow matrix passed: "
        f"{len(REQUIRED_WORKFLOW_ROWS)} workflow categories and {len(REQUIRED_MARKERS)} release markers present."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())