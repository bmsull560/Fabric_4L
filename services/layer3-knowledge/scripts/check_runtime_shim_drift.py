#!/usr/bin/env python3
"""Fail CI if Layer 3 runtime compatibility modules drift from shim forwarders."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


EXPECTED: dict[str, str] = {
    "services/layer3-knowledge/src/api/models.py": (
        '"""Layer 3 compatibility shim for API models.\n\n'
        'This module intentionally re-exports the canonical Layer 3 API models from\n'
        '``value_fabric.layer3.api.models`` and must not contain service-local business\n'
        'logic.\n"""\n\n'
        'from value_fabric.layer3.api.models import *  # noqa: F401,F403\n'
    ),
    "services/layer3-knowledge/src/api/app_monolith.py": (
        '"""Allowed service-local exception for Layer 3 service wrapper.\n\n'
        'Owner: layer3-knowledge\n'
        'Removal/migration target: 2026-09-30\n'
        'Reason: Service-wrapper-only logic permitted by runtime path governance.\n"""\n\n\n'
        'from value_fabric.layer3.api.app_monolith import *  # noqa: F401,F403\n'
    ),
    "services/layer3-knowledge/src/services/product_service.py": (
        '"""Compatibility wrapper for value_fabric.layer3.services.product_service."""\n\n'
        'from value_fabric.layer3.services.product_service import *  # noqa: F401,F403\n'
    ),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail CI if Layer 3 runtime compatibility modules drift from shim forwarders."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Repository root directory (default: auto-detected)",
    )
    args = parser.parse_args(argv)

    repo_root: Path = args.repo_root
    drifted: list[str] = []
    for rel_path, expected in EXPECTED.items():
        file_path = repo_root / rel_path
        if not file_path.exists():
            drifted.append(f"MISSING: {rel_path}")
            continue
        try:
            actual = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            drifted.append(f"READ_ERROR: {rel_path} ({exc})")
            continue
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
