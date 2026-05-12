#!/usr/bin/env python3
"""Fail CI if Layer 3 backup compatibility shims drift from canonical forwarders."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]

EXPECTED = {
    "services/layer3-knowledge/src/backup/backup_manager.py": (
        '"""Compatibility forwarder for Layer 3 backup manager.\n\n'
        'Canonical implementation lives in ``value_fabric.layer3.backup.backup_manager``.\n"""\n\n'
        'from value_fabric.layer3.backup.backup_manager import *  # noqa: F403\n'
    ),
    "services/layer3-knowledge/src/backup/__init__.py": (
        '"""Compatibility forwarder for Layer 3 backup package.\n\n'
        'Canonical implementation lives in ``value_fabric.layer3.backup``.\n"""\n\n'
        'from value_fabric.layer3.backup import *  # noqa: F403\n'
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
        print("Layer 3 backup compatibility shim drift detected:", file=sys.stderr)
        for item in drifted:
            print(f" - {item}", file=sys.stderr)
        print(
            "Keep canonical logic in value_fabric/layer3/backup/ and preserve service wrappers as thin forwarders.",
            file=sys.stderr,
        )
        return 1

    print("Layer 3 backup compatibility shim check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
