from __future__ import annotations

import re
from pathlib import Path


def _active_milestones() -> list[str]:
    milestones_doc = Path("docs/contracts/layer6-audit-artifacts/active-milestones.md")
    text = milestones_doc.read_text(encoding="utf-8")
    return re.findall(r"-\s+`([^`]+)`", text)


def test_layer6_active_milestones_have_required_artifacts() -> None:
    base = Path("docs/contracts/layer6-audit-artifacts/milestones")
    milestones = _active_milestones()

    assert milestones, "No active Layer 6 drift-audit milestones are declared."

    missing: list[str] = []
    for milestone in milestones:
        report = base / milestone / "report.md"
        checklist = base / milestone / "checklist.md"
        if not report.exists():
            missing.append(str(report))
        if not checklist.exists():
            missing.append(str(checklist))

    assert not missing, (
        "Missing required Layer 6 drift-audit artifact files for active milestones: "
        + ", ".join(missing)
    )


def test_layer6_drift_audit_template_has_required_sections() -> None:
    template = Path("docs/contracts/layer6-audit-artifacts/TEMPLATE.md").read_text(encoding="utf-8")

    required_sections = [
        "## Endpoint inventory",
        "## Frontend usage mapping",
        "## Gateway exposure matrix",
        "## Risk classification",
        "## Owner sign-off block",
    ]

    missing_sections = [section for section in required_sections if section not in template]
    assert not missing_sections, (
        "Layer 6 drift-audit template is missing required sections: "
        + ", ".join(missing_sections)
    )
