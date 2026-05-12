from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "repro-seeds" / "runner.py"
VALIDATOR = ROOT / "scripts" / "repro-seeds" / "validate_seed_packs.py"
PACK = ROOT / "tests" / "repro-seeds" / "packs" / "seed-l4-incident-2026-001"


def test_runner_applies_seed_pack(tmp_path: Path) -> None:
    manifest = json.loads((PACK / "manifest.json").read_text())
    cmd = [
        sys.executable,
        str(RUNNER),
        "--pack-dir",
        str(PACK),
        "--migration-revision",
        manifest["required_migration_revision"],
        "--output-dir",
        str(tmp_path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    assert payload["sha256"]


def test_validator_passes() -> None:
    subprocess.run([sys.executable, str(VALIDATOR)], check=True)
