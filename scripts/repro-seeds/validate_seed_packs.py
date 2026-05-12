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


def _run_once(pack_dir: Path, out_dir: Path) -> str:
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
    return json.loads(result.stdout)["sha256"]


def validate_pack(pack_dir: Path) -> None:
    payload_text = (pack_dir / "payload.json").read_text()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in payload_text:
            raise AssertionError(f"Forbidden pattern '{pattern}' found in {pack_dir}/payload.json")

    manifest = json.loads((pack_dir / "manifest.json").read_text())
    payload = json.loads((pack_dir / "payload.json").read_text())
    if payload.get("tenant_id") not in manifest["tenant_scope"]:
        raise AssertionError(f"payload tenant_id must be in tenant_scope for {pack_dir.name}")

    with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
        sha1 = _run_once(pack_dir, Path(t1))
        sha2 = _run_once(pack_dir, Path(t2))
    if sha1 != sha2:
        raise AssertionError(f"Determinism check failed for {pack_dir.name}: {sha1} != {sha2}")


def main() -> None:
    for pack_dir in sorted(PACKS_ROOT.iterdir()):
        if pack_dir.is_dir():
            validate_pack(pack_dir)
    print("All seed packs passed deterministic + tenant-safe checks.")


if __name__ == "__main__":
    main()
