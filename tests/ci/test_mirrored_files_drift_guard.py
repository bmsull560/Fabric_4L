from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_mirrored_files_guard_passes() -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "check_mirrored_files.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, cwd=root)
    assert result.returncode == 0, result.stdout + result.stderr

def test_layer6_wrapper_drift_guard_passes() -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "ci" / "check_layer6_wrapper_drift.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, cwd=root)
    assert result.returncode == 0, result.stdout + result.stderr


def test_layer6_wrapper_manifest_covers_service_tree() -> None:
    root = Path(__file__).resolve().parents[2]
    config = root / "scripts" / "mirrored_files.json"
    wrapper_entries = json.loads(config.read_text())["wrapper_files"]

    declared_paths = {item["path"] for item in wrapper_entries}
    service_paths = {
        path.relative_to(root).as_posix()
        for path in (root / "services" / "layer6-benchmarks" / "src").rglob("*.py")
    }

    assert declared_paths == service_paths, (
        "Layer 6 wrapper manifest must cover the full service-local wrapper tree.\n"
        f"Declared only: {sorted(declared_paths - service_paths)}\n"
        f"Undeclared files: {sorted(service_paths - declared_paths)}"
    )


def test_layer6_wrapper_manifest_targets_canonical_modules() -> None:
    root = Path(__file__).resolve().parents[2]
    config = root / "scripts" / "mirrored_files.json"
    wrapper_entries = json.loads(config.read_text())["wrapper_files"]

    invalid = [
        item["module"]
        for item in wrapper_entries
        if not item["module"].startswith("value_fabric.layer6")
    ]
    assert not invalid, f"Layer 6 wrapper manifest contains non-canonical targets: {invalid}"
