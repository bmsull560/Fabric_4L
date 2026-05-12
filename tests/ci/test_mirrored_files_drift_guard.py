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

def test_layer6_critical_mirror_coverage() -> None:
    root = Path(__file__).resolve().parents[2]
    config = root / "scripts" / "mirrored_files.json"
    mirrored = json.loads(config.read_text())["mirrored_pairs"]

    by_pair = {(item["canonical"], item["mirror"]) for item in mirrored}

    required = {
        ("value_fabric/layer6/api/main.py", "services/layer6-benchmarks/src/api/main.py"),
        ("value_fabric/layer6/api/routes/benchmarks.py", "services/layer6-benchmarks/src/api/routes/benchmarks.py"),
        ("value_fabric/layer6/api/routes/system.py", "services/layer6-benchmarks/src/api/routes/system.py"),
        ("value_fabric/layer6/repositories/benchmark_repository.py", "services/layer6-benchmarks/src/repositories/benchmark_repository.py"),
        ("value_fabric/layer6/models/benchmark_dataset.py", "services/layer6-benchmarks/src/models/benchmark_dataset.py"),
        ("value_fabric/layer6/database.py", "services/layer6-benchmarks/src/database.py"),
    }

    missing = required - by_pair
    assert not missing, f"Layer 6 critical mirror mappings missing: {sorted(missing)}"
