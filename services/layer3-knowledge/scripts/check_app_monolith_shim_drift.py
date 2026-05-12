#!/usr/bin/env python3
"""Ensure Layer 3 app_monolith compatibility shim remains a thin forwarder."""

from __future__ import annotations

from pathlib import Path
import hashlib
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_PATH = REPO_ROOT / "value_fabric/layer3/api/app_monolith.py"
COMPAT_PATH = REPO_ROOT / "services/layer3-knowledge/src/api/app_monolith.py"
EXPECTED_SHIM = '''"""Compatibility shim for the canonical Layer 3 API monolith.

Authoritative implementation lives in ``value_fabric.layer3.api.app_monolith``
per docs/reference/layer-runtime-path-governance.md.
Do not add business logic in this compatibility module.
"""

from value_fabric.layer3.api.app_monolith import *  # noqa: F401,F403
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []

    if not CANONICAL_PATH.exists():
        errors.append(f"Missing canonical module: {CANONICAL_PATH}")

    if not COMPAT_PATH.exists():
        errors.append(f"Missing compatibility module: {COMPAT_PATH}")
    else:
        actual = COMPAT_PATH.read_text(encoding="utf-8")
        if actual != EXPECTED_SHIM:
            errors.append(
                "Compatibility shim drift detected in services/layer3-knowledge/src/api/app_monolith.py. "
                "Keep this file as a thin re-export only."
            )

    if errors:
        for msg in errors:
            print(f"ERROR: {msg}")
        return 1

    print(
        "Layer 3 app_monolith shim verified. "
        f"canonical_sha256={sha256(CANONICAL_PATH)} compat_sha256={sha256(COMPAT_PATH)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
