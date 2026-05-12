#!/usr/bin/env python3
"""Generate Layer 5 OpenAPI, normalize it, and diff against committed contract."""

from __future__ import annotations

import difflib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = REPO_ROOT / "services" / "layer5-ground-truth"
CANONICAL_SRC = SERVICE_ROOT / "src"
CONTRACT_PATH = REPO_ROOT / "contracts" / "openapi" / "layer5-ground-truth.json"


def _normalize_json(payload: object) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _load_runtime_openapi() -> object:
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(CANONICAL_SRC))
    from layer5_ground_truth.api.main import app  # pylint: disable=import-outside-toplevel

    return app.openapi()


def main() -> int:
    generated_openapi = _load_runtime_openapi()
    normalized_generated = _normalize_json(generated_openapi)

    if not CONTRACT_PATH.exists():
        print(f"Contract file missing: {CONTRACT_PATH}", file=sys.stderr)
        return 1

    normalized_committed = _normalize_json(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))

    if normalized_generated == normalized_committed:
        print("Layer 5 OpenAPI contract is up to date.")
        return 0

    diff = difflib.unified_diff(
        normalized_committed.splitlines(keepends=True),
        normalized_generated.splitlines(keepends=True),
        fromfile=str(CONTRACT_PATH),
        tofile="generated:layer5_ground_truth.api.main:app.openapi()",
    )
    print("".join(diff), end="")
    print(
        "\nOpenAPI drift detected for Layer 5. "
        "Regenerate contracts/openapi/layer5-ground-truth.json from canonical runtime source and commit it.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
