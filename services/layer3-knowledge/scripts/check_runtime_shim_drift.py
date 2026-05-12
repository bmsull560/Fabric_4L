#!/usr/bin/env python3
"""Fail CI if Layer 3 runtime compatibility modules drift from shim forwarders."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


EXPECTED: dict[str, str] = {
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
