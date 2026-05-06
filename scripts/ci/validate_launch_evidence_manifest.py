#!/usr/bin/env python3
"""Validate a release launch evidence manifest without storing secrets.

The manifest distinguishes repository-owned readiness from launch-environment
evidence. It may be used against the checked-in example, a release-candidate
manifest, or a redacted artifact path supplied by CI.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

REQUIRED_GATES = {
    "production_like_e2e",
    "enterprise_sso_oidc",
    "rollback_restore",
    "telemetry_alerting",
    "billing_metering",
    "performance_smoke",
}
ALLOWED_STATUSES = {"REQUIRES_ENVIRONMENT", "PASS_WITH_EVIDENCE", "FAIL", "WAIVED"}


def _load_manifest(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("manifest root must be a mapping")
    return loaded


def validate_manifest(path: Path) -> list[str]:
    manifest = _load_manifest(path)
    errors: list[str] = []

    gates = manifest.get("gates")
    if not isinstance(gates, dict):
        return ["manifest must contain a gates mapping"]

    missing = sorted(REQUIRED_GATES - set(gates))
    if missing:
        errors.append(f"missing launch evidence gates: {missing}")

    allowed_from_manifest = manifest.get("allowed_statuses", sorted(ALLOWED_STATUSES))
    allowed = set(allowed_from_manifest if isinstance(allowed_from_manifest, list) else [])
    if allowed != ALLOWED_STATUSES:
        errors.append(f"allowed_statuses must be exactly {sorted(ALLOWED_STATUSES)}")

    for name, gate in sorted(gates.items()):
        if not isinstance(gate, dict):
            errors.append(f"{name}: gate entry must be a mapping")
            continue

        status = gate.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{name}: invalid status {status!r}")
            continue

        owner = gate.get("owner")
        acceptance = gate.get("acceptance")
        if not isinstance(owner, str) or not owner.strip():
            errors.append(f"{name}: owner is required")
        if not isinstance(acceptance, str) or not acceptance.strip():
            errors.append(f"{name}: acceptance criteria are required")
        if status == "PASS_WITH_EVIDENCE" and not gate.get("evidence_uri"):
            errors.append(f"{name}: PASS_WITH_EVIDENCE requires evidence_uri")
        if status == "WAIVED" and not gate.get("waiver_uri"):
            errors.append(f"{name}: WAIVED requires waiver_uri")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_launch_evidence_manifest.py <manifest.yaml>")
        return 2

    path = Path(argv[1])
    if not path.exists():
        print(f"launch evidence manifest not found: {path}")
        return 1

    try:
        errors = validate_manifest(path)
    except Exception as exc:  # noqa: BLE001 - CLI should surface parse failures clearly.
        print(f"failed to parse launch evidence manifest: {exc}")
        return 1

    if errors:
        print("launch evidence manifest validation failed:")
        print("\n".join(f"  - {error}" for error in errors))
        return 1

    print("launch evidence manifest schema OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
