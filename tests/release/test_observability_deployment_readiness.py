"""Release gate: observability/deployment readiness must be fully verified.

Enforces that release-tag workflows cannot proceed if any Task 46/47
readiness row is missing PASS status, verification date, or evidence artifact link.
"""

from __future__ import annotations

import re
from pathlib import Path

READINESS_DOC = Path("docs/readiness/observability-deployment-readiness.md")


class TestObservabilityDeploymentReadiness:
    def test_readiness_doc_exists(self) -> None:
        assert READINESS_DOC.exists(), f"Missing readiness document: {READINESS_DOC}"

    def test_no_tbd_or_partial_statuses(self) -> None:
        content = READINESS_DOC.read_text(encoding="utf-8")
        assert "TBD" not in content
        assert "Partial" not in content
        assert "🟡" not in content

    def test_all_check_rows_are_pass_with_dates_and_artifacts(self) -> None:
        content = READINESS_DOC.read_text(encoding="utf-8")
        check_rows = [line for line in content.splitlines() if line.startswith("| ") and "---" not in line and "Check" not in line]
        assert check_rows, "Expected readiness check rows in markdown tables"

        date_pattern = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
        path_pattern = re.compile(r"`([^`]+)`")

        for row in check_rows:
            assert "✅ PASS" in row, f"Row is not PASS: {row}"
            assert date_pattern.search(row), f"Row missing ISO verification date: {row}"
            cols = [c.strip() for c in row.strip().split("|")]
            assert len(cols) >= 5, f"Unexpected table row format: {row}"
            artifacts_col = cols[4]
            artifacts = path_pattern.findall(artifacts_col)
            assert artifacts, f"Row missing evidence artifacts: {row}"
            for artifact in artifacts:
                artifact_root = artifact.split(" (")[0]
                assert Path(artifact_root).exists(), f"Evidence path does not exist: {artifact_root}"
