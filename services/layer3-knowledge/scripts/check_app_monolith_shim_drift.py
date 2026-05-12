#!/usr/bin/env python3
"""Ensure Layer 3 app_monolith compatibility shim remains a thin forwarder."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


EXPECTED_SHIM = '''"""Allowed service-local exception for Layer 3 service wrapper.

Owner: layer3-knowledge
Removal/migration target: 2026-09-30
Reason: Service-wrapper-only logic permitted by runtime path governance.
"""


from value_fabric.layer3.api.app_monolith import *  # noqa: F401,F403
'''


def _sha256(path: Path) -> str | None:
    """Return hex digest of file contents, or None on read error."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        print(f"WARNING: cannot read {path}: {exc}", file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ensure Layer 3 app_monolith compatibility shim remains a thin forwarder."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Repository root directory (default: auto-detected)",
    )
    args = parser.parse_args(argv)

    repo_root: Path = args.repo_root
    canonical_path = repo_root / "value_fabric" / "layer3" / "api" / "app_monolith.py"
    compat_path = repo_root / "services" / "layer3-knowledge" / "src" / "api" / "app_monolith.py"

    errors: list[str] = []

    if not canonical_path.exists():
        errors.append(f"Missing canonical module: {canonical_path}")

    if not compat_path.exists():
        errors.append(f"Missing compatibility module: {compat_path}")
    else:
        try:
            actual = compat_path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"Cannot read compatibility module: {exc}")
        else:
            if actual != EXPECTED_SHIM:
                errors.append(
                    "Compatibility shim drift detected in services/layer3-knowledge/src/api/app_monolith.py. "
                    "Keep this file as a thin re-export only."
                )

    if errors:
        for msg in errors:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    canonical_hash = _sha256(canonical_path)
    compat_hash = _sha256(compat_path)
    print(
        "Layer 3 app_monolith shim verified. "
        f"canonical_sha256={canonical_hash or 'N/A'} compat_sha256={compat_hash or 'N/A'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
