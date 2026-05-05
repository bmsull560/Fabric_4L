#!/usr/bin/env python3
"""Fail closed if backend/platform validation ownership loses release-critical evidence markers."""

from __future__ import annotations

import sys
from pathlib import Path


MATRIX_PATH = Path("docs/validation/backend_platform_validation_ownership_matrix.md")
MASTER_MATRIX_PATH = Path("docs/validation/master_workflow_traceability_matrix.md")
BACKEND_CONTRACT_PATH = Path("docs/contracts/workflow-traceability-matrix.md")
BACKEND_INTEGRATED_PATH = Path(
    "docs/validation/backend_integrated/backend_integrated_traceability_matrix.md"
)

REQUIRED_SECTIONS = [
    "## Matrix Maintenance Contract",
    "## Release Ownership Summary",
    "## Backend and Platform Evidence Matrix",
    "## Gate Integration",
    "## Open Implementation Backlog",
]

REQUIRED_GAP_MARKERS = {
    "SSO/MFA ownership": "SSO/MFA and session policy",
    "ingestion persistence ownership": "Ingestion job persistence and recovery",
    "audit immutability ownership": "Audit immutability and approval lineage",
    "observability ownership": "Observability and release health",
    "retention enforcement ownership": "Retention and deletion policy enforcement",
    "real external integrations ownership": "Real external integration behavior",
}

REQUIRED_EVIDENCE_MARKERS = {
    "auth enforcement tests": "services/api/app/tests/test_auth_enforcement.py",
    "production safety tests": "services/api/app/tests/test_production_safety.py",
    "durable persistence tests": "services/api/app/tests/test_i03_durable_persistence_and_llm.py",
    "health metrics tests": "services/api/app/tests/test_health.py",
    "tenant persistence suite": "tests/backend_integrated/test_tenant_isolation_security_persistence.py",
    "cross-layer data flow suite": "tests/backend_integrated/test_cross_layer_data_flow_validation.py",
    "operational resilience suite": "tests/backend_integrated/test_operational_resilience_real_services.py",
    "approval export crm suite": "tests/backend_integrated/test_approval_export_crm_governance.py",
    "calculation provenance suite": "tests/backend_integrated/test_calculation_evidence_provenance_integrity.py",
    "release smoke suite": "tests/backend_integrated/test_release_environment_smoke_validation.py",
    "backend integrated gate": "make test-backend-integrated-validation",
    "release smoke gate": "make test-backend-integrated-release-smoke",
    "workflow matrix gate": "make check-workflow-matrix",
    "direct ownership guard": "python3 scripts/ci/assert_backend_platform_validation_ownership.py",
}

REQUIRED_BACKLOG_MARKERS = {
    "release IdP SSO/MFA smoke": "release IdP SSO/MFA smoke",
    "retention policy tests": "retention and deletion policy tests",
    "restart-safe ingestion recovery": "restart-safe ingestion job recovery checks",
    "append-only audit assertions": "append-only audit immutability assertions",
    "trace identifier recommendation": "trace_id",
}

REQUIRED_CROSS_LINKS = {
    MASTER_MATRIX_PATH: "docs/validation/backend_platform_validation_ownership_matrix.md",
    BACKEND_CONTRACT_PATH: "docs/validation/backend_platform_validation_ownership_matrix.md",
    BACKEND_INTEGRATED_PATH: "docs/validation/backend_platform_validation_ownership_matrix.md",
}


def collect_missing_markers(text: str) -> list[str]:
    failures: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in text:
            failures.append(f"Missing section: {section}")

    for label, marker in REQUIRED_GAP_MARKERS.items():
        if marker not in text:
            failures.append(f"Missing {label}: {marker}")

    for label, marker in REQUIRED_EVIDENCE_MARKERS.items():
        if marker not in text:
            failures.append(f"Missing {label}: {marker}")

    for label, marker in REQUIRED_BACKLOG_MARKERS.items():
        if marker not in text:
            failures.append(f"Missing {label}: {marker}")

    return failures


def collect_missing_cross_links() -> list[str]:
    failures: list[str] = []

    for path, marker in REQUIRED_CROSS_LINKS.items():
        if not path.exists():
            failures.append(f"Missing cross-link host document: {path}")
            continue
        content = path.read_text(encoding="utf-8")
        if marker not in content:
            failures.append(f"Missing backend/platform ownership cross-link in {path}: {marker}")

    return failures


def main() -> int:
    if not MATRIX_PATH.exists():
        print(f"Missing backend/platform validation ownership matrix: {MATRIX_PATH}", file=sys.stderr)
        return 1

    matrix = MATRIX_PATH.read_text(encoding="utf-8")
    failures = collect_missing_markers(matrix)
    failures.extend(collect_missing_cross_links())

    if failures:
        print(
            f"Backend/platform validation ownership matrix is incomplete: {MATRIX_PATH}",
            file=sys.stderr,
        )
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1

    marker_count = (
        len(REQUIRED_SECTIONS)
        + len(REQUIRED_GAP_MARKERS)
        + len(REQUIRED_EVIDENCE_MARKERS)
        + len(REQUIRED_BACKLOG_MARKERS)
        + len(REQUIRED_CROSS_LINKS)
    )
    print(
        "Backend/platform validation ownership matrix passed: "
        f"{marker_count} release ownership markers and cross-links present."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
