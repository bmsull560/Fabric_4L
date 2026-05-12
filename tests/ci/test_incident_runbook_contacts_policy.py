from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK_PATH = REPO_ROOT / "docs/operations/runbook-overview.md"
INCIDENT_CRITICAL_HEADERS = (
    "## Contact Information",
    "### Security Incident Response",
    "### Incident Response Procedure",
)


def _section_text(content: str, header: str) -> str:
    start = content.find(header)
    if start == -1:
        return ""
    remaining = content[start + len(header) :]
    next_header_index = remaining.find("\n## ")
    return remaining if next_header_index == -1 else remaining[:next_header_index]


def test_incident_critical_sections_have_no_tbd_placeholders() -> None:
    content = RUNBOOK_PATH.read_text(encoding="utf-8")

    offending_headers: list[str] = []
    for header in INCIDENT_CRITICAL_HEADERS:
        section = _section_text(content, header)
        if "TBD" in section:
            offending_headers.append(header)

    assert not offending_headers, (
        "TBD placeholders remain in incident-critical runbook sections: "
        + ", ".join(offending_headers)
    )
