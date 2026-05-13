"""Validate the cross-layer tenant isolation matrix artifact."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: validate_cross_layer_tenant_matrix.py <artifact-path>", file=sys.stderr)
        return 2

    artifact_path = Path(argv[1])
    if not artifact_path.exists():
        print(f"Missing cross-layer tenant matrix artifact: {artifact_path}", file=sys.stderr)
        return 1

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    overall_status = payload.get("overall_status")
    missing_coverage = payload.get("missing_coverage", [])
    results = payload.get("results", [])
    failed = [result for result in results if result.get("status") != "PASS"]

    if overall_status != "PASS":
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    if missing_coverage:
        print(json.dumps({"missing_coverage": missing_coverage}, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    if failed:
        print(json.dumps({"failed_controls": failed}, indent=2, sort_keys=True), file=sys.stderr)
        return 1

    print(f"Validated cross-layer tenant matrix artifact: {artifact_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
