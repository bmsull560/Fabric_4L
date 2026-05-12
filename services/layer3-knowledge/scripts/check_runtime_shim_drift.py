#!/usr/bin/env python3
"""Fail CI if Layer 3 runtime compatibility modules drift from shim forwarders."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]

EXPECTED = {
    "services/layer3-knowledge/src/api/models.py": (
        '"""Compatibility forwarder for Layer 3 API models.\n\n'
        'Canonical implementation lives in ``value_fabric.layer3.api.models``.\n"""\n\n'
        'from value_fabric.layer3.api.models import *  # noqa: F403\n'
    ),
    "services/layer3-knowledge/src/api/app_monolith.py": (
        '"""Compatibility forwarder for Layer 3 monolith app module.\n\n'
        'Canonical implementation lives in ``value_fabric.layer3.api.app_monolith``.\n"""\n\n'
        'from value_fabric.layer3.api.app_monolith import *  # noqa: F403\n'
    ),
    "services/layer3-knowledge/src/services/product_service.py": (
        '"""Compatibility forwarder for Layer 3 product service.\n\n'
        'Canonical implementation lives in ``value_fabric.layer3.services.product_service``.\n"""\n\n'
        'from value_fabric.layer3.services.product_service import *  # noqa: F403\n'
    ),
}


def main() -> int:
    drifted: list[str] = []
    for rel_path, expected in EXPECTED.items():
        file_path = REPO_ROOT / rel_path
        if not file_path.exists():
            drifted.append(f"MISSING: {rel_path}")
            continue
        actual = file_path.read_text(encoding="utf-8")
        if actual != expected:
            drifted.append(f"DRIFT: {rel_path}")

    if drifted:
        print("Layer 3 runtime compatibility shim drift detected:", file=sys.stderr)
        for item in drifted:
            print(f" - {item}", file=sys.stderr)
        print(
            "Keep canonical runtime logic in value_fabric/layer3/ and preserve service wrappers as thin forwarders.",
            file=sys.stderr,
        )
        return 1

    print("Layer 3 runtime compatibility shim check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
