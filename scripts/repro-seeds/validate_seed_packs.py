#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKS_ROOT = ROOT / "tests" / "repro-seeds" / "packs"
RUNNER = ROOT / "scripts" / "repro-seeds" / "runner.py"

FORBIDDEN_PATTERNS = ["@acme.com", "Alice Carter", "tenant-", "api_key", "Bearer "]
REQUIRED_MANIFEST_FIELDS = {
    "seed_id",
    "source_incident_ticket",
    "affected_layers",
    "required_migration_revision",
    "deterministic_rng_seed",
    "anonymization_profile",
    "tenant_scope",
}


def _run_once(pack_dir: Path, out_dir: Path) -> tuple[str, Path]:
    manifest = json.loads((pack_dir / "manifest.json").read_text())
    cmd = [
        sys.executable,
        str(RUNNER),
        "--pack-dir",
        str(pack_dir),
        "--migration-revision",
        manifest["required_migration_revision"],
        "--output-dir",
        str(out_dir),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return data["sha256"], Path(data["output"])


def _validate_manifest(manifest: dict[str, object], pack_dir: Path) -> None:
    missing = REQUIRED_MANIFEST_FIELDS - set(manifest)
    if missing:
        raise AssertionError(f"Manifest missing required fields in {pack_dir.name}: {sorted(missing)}")


def validate_pack(pack_dir: Path) -> None:
    payload_text = (pack_dir / "payload.json").read_text()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in payload_text:
            raise AssertionError(f"Forbidden pattern '{pattern}' found in {pack_dir}/payload.json")

    manifest = json.loads((pack_dir / "manifest.json").read_text())
    _validate_manifest(manifest, pack_dir)

    payload = json.loads((pack_dir / "payload.json").read_text())
    if payload.get("tenant_id") not in manifest["tenant_scope"]:
        raise AssertionError(f"payload tenant_id must be in tenant_scope for {pack_dir.name}")

    expected_output_path = pack_dir / "expected-output.json"
    if not expected_output_path.exists():
        raise AssertionError(f"Missing expected-output.json for {pack_dir.name}")

    with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
        sha1, output1 = _run_once(pack_dir, Path(t1))
        sha2, _ = _run_once(pack_dir, Path(t2))
        if sha1 != sha2:
            raise AssertionError(f"Determinism check failed for {pack_dir.name}: {sha1} != {sha2}")

        expected = json.loads(expected_output_path.read_text())
        generated = json.loads(output1.read_text())
        if expected != generated:
            raise AssertionError(
                f"Expected output drift for {pack_dir.name}; regenerate expected-output.json intentionally."
            )


def main() -> None:
    for pack_dir in sorted(PACKS_ROOT.iterdir()):
        if pack_dir.is_dir():
            validate_pack(pack_dir)
    print("All seed packs passed manifest, deterministic, expected-output, and tenant-safe checks.")


if __name__ == "__main__":
    main()
