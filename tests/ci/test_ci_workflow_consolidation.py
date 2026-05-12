from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"
PLAN = REPO_ROOT / "docs" / "operations" / "ci-workflow-consolidation.md"

CANONICAL_WORKFLOWS = {
    "pr-checks.yml",
    "security-gates.yml",
    "contract-compliance.yml",
    "launch-readiness.yml",
}

DEPRECATION_CANDIDATES = {
    "test.yml": "Legacy monolithic test workflow",
    "critical-gates.yml": "Overlaps auth coverage, tenant isolation, OpenAPI drift, and config gates",
    "prod-readiness.yml": "Older production-readiness gate",
}


def test_ci_workflow_consolidation_plan_names_canonical_owners() -> None:
    content = PLAN.read_text(encoding="utf-8")

    for workflow in CANONICAL_WORKFLOWS:
        assert workflow in content
        assert (WORKFLOW_DIR / workflow).exists(), f"Missing canonical workflow: {workflow}"


def test_ci_workflow_deprecation_candidates_are_documented_but_still_enabled() -> None:
    content = PLAN.read_text(encoding="utf-8")

    for workflow, reason in DEPRECATION_CANDIDATES.items():
        path = WORKFLOW_DIR / workflow
        assert path.exists(), f"Missing deprecation candidate workflow: {workflow}"
        assert workflow in content
        assert reason in content

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert data.get("on") or data.get(True), f"{workflow} should remain enabled until replacement proof exists"


def test_ci_workflow_cleanup_rules_preserve_required_gate_visibility() -> None:
    content = PLAN.read_text(encoding="utf-8")

    required_rules = [
        "Do not delete or disable a workflow",
        "Do not rename required workflow or job names",
        "Keep security and contract gates visible",
    ]
    for rule in required_rules:
        assert rule in content
