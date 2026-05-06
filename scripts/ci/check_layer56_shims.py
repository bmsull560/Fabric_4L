#!/usr/bin/env python3
"""CI guard: ensure selected service mirror files remain shim-only adapters."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]

SHIMS = {
    "services/layer6-benchmarks/src/config.py": "from value_fabric.layer6.config import *",
    "services/layer6-benchmarks/src/database.py": "from value_fabric.layer6.database import *",
    "services/layer6-benchmarks/src/shared_bootstrap.py": "from value_fabric.layer6.shared_bootstrap import *",
    "services/layer6-benchmarks/src/metrics/prometheus_metrics.py": "from value_fabric.layer6.metrics.prometheus_metrics import *",
}


def main() -> int:
    failures: list[str] = []
    for rel, expected in SHIMS.items():
        path = REPO_ROOT / rel
        if not path.exists():
            failures.append(f"Missing shim file: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if expected not in text:
            failures.append(f"Shim does not re-export canonical module: {rel}")
        body = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith('"""')]
        if len(body) > 2:
            failures.append(f"Shim must stay thin (no local logic): {rel}")

    if failures:
        print("ERROR: layer shim guard failed")
        for item in failures:
            print(f" - {item}")
        return 1

    print("OK: selected layer mirror files are shim-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
