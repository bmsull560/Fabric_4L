#!/usr/bin/env python3
"""Generate machine-readable audit evidence snapshot artifacts under docs/audit/."""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = ROOT / "docs" / "audit" / "snapshots"

CHECKS = [
    {
        "name": "control_matrix_exists",
        "command": ["test", "-f", "docs/trust/control-matrix.v1.yaml"],
    },
    {
        "name": "retention_contract_test_exists",
        "command": ["test", "-f", "tests/contracts/test_retention_deletion_contract.py"],
    },
    {
        "name": "audit_events_migration_exists",
        "command": ["test", "-f", "services/layer4-agents/migrations/versions/003_add_audit_events.py"],
    },
]


def run_check(command: list[str]) -> dict[str, object]:
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    results = []
    for check in CHECKS:
        execution = run_check(check["command"])
        results.append(
            {
                "name": check["name"],
                "command": " ".join(check["command"]),
                "status": "pass" if execution["returncode"] == 0 else "fail",
                **execution,
            }
        )

    snapshot = {
        "generated_at": generated_at,
        "policy_state": {
            "gdpr_enabled": True,
            "hipaa_mode": "conditional_if_phi_processed",
        },
        "checks": results,
    }

    target = AUDIT_DIR / f"audit-snapshot-{generated_at.replace(':', '').replace('+00:00', 'Z')}.json"
    target.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    (AUDIT_DIR / "latest.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(target.relative_to(ROOT))


if __name__ == "__main__":
    main()
