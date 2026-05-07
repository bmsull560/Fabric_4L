from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run(script: Path, collection_file: Path, allowlist_file: Path, baseline_file: Path, report_file: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(script),
            str(collection_file),
            "--allowlist",
            str(allowlist_file),
            "--baseline",
            str(baseline_file),
            "--write-report",
            str(report_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_infra_skip_allowed_and_code_health_violates(tmp_path: Path) -> None:
    script = Path("scripts/ci/check_pytest_skip_governance.py")
    collection_file = tmp_path / "collection.txt"
    allowlist_file = tmp_path / "allowlist.yaml"
    baseline_file = tmp_path / "baseline.json"
    report_file = tmp_path / "report.json"

    collection_file.write_text(
        "\n".join(
            [
                "SKIPPED [1] tests/security/conftest.py: redis not installed",
                "SKIPPED [1] tests/foo.py: import path unresolved for legacy module",
            ]
        ),
        encoding="utf-8",
    )
    allowlist_file.write_text("allowlist: []\n", encoding="utf-8")
    baseline_file.write_text(json.dumps({"max_total_skips": 10, "max_category_skips": {"infrastructure": 10}}), encoding="utf-8")

    proc = _run(script, collection_file, allowlist_file, baseline_file, report_file)
    assert proc.returncode == 1
    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert report["category_counts"]["infrastructure"] == 1
    assert report["category_counts"]["code_health"] == 1
    assert any(v["category"] == "code_health" for v in report["violations"])
