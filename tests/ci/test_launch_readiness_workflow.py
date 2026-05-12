from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "launch-readiness.yml"


def _workflow() -> dict:
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_launch_readiness_workflow_is_stage_gated() -> None:
    workflow = _workflow()
    jobs = workflow["jobs"]

    assert "stage-1-baseline" in jobs
    assert "stage-2-frontend-tests" in jobs
    assert "stage-2-journey-smoke" in jobs
    assert "stage-3-contract-security" in jobs
    assert "stage-4-evidence-archive" in jobs
    assert "stage-5-staging-evidence" in jobs
    assert jobs["stage-2-frontend-tests"]["needs"] == "stage-1-baseline"
    assert set(jobs["stage-3-contract-security"]["needs"]) == {"stage-2-frontend-tests", "stage-2-journey-smoke"}
    assert jobs["stage-4-evidence-archive"]["needs"] == "stage-3-contract-security"
    assert jobs["stage-5-staging-evidence"]["needs"] == "stage-4-evidence-archive"


def test_launch_readiness_workflow_is_artifact_only_no_ci_push() -> None:
    content = WORKFLOW.read_text(encoding="utf-8")
    workflow = _workflow()

    assert workflow["permissions"]["contents"] == "read"
    assert "contents: write" not in content
    assert "git push" not in content
    assert "git commit" not in content
    assert "upload-artifact" in content
    assert "generate_launch_evidence_bundle.py" in content


def test_launch_readiness_workflow_uses_expected_stage_inputs() -> None:
    content = WORKFLOW.read_text(encoding="utf-8")

    for stage in ("baseline", "local_quality", "contract_security", "evidence_archive", "staging"):
        assert stage in content
    assert "--up-to-stage evidence_archive" in content
    assert "environment: staging" in content


def test_pnpm_is_setup_before_setup_node_pnpm_cache() -> None:
    workflow = _workflow()
    violations: list[str] = []

    for job_name, job in workflow["jobs"].items():
        pnpm_setup_seen = False
        for step in job.get("steps", []):
            if not isinstance(step, dict):
                continue

            uses = str(step.get("uses", ""))
            if uses.startswith("pnpm/action-setup@"):
                pnpm_setup_seen = True

            with_config = step.get("with") or {}
            if (
                uses.startswith("actions/setup-node@")
                and isinstance(with_config, dict)
                and with_config.get("cache") == "pnpm"
                and not pnpm_setup_seen
            ):
                violations.append(job_name)

    assert not violations, "setup-node pnpm cache appears before pnpm setup in: " + ", ".join(violations)


def test_launch_pipeline_does_not_reference_generated_bytecode() -> None:
    content = WORKFLOW.read_text(encoding="utf-8")
    script_text = (REPO_ROOT / "scripts" / "ci" / "generate_launch_evidence_bundle.py").read_text(encoding="utf-8")

    assert "__pycache__" not in content
    assert ".pyc" not in content
    assert "__pycache__" not in script_text
    assert ".pyc" not in script_text
