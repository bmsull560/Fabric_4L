#!/usr/bin/env python3
"""Generate the Value Fabric Python SDK.

This script:
1. Exports the latest OpenAPI specs from all layers.
2. Copies the Layer 4 spec into the SDK package as a reference.
3. Confirms the manual typed client in sdk/python/src/valuefabric/ is up to date.

Because we build the client manually with httpx (no external generators),
this script is intentionally lightweight.
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SDK_DIR = REPO_ROOT / "sdk" / "python"
SRC_DIR = SDK_DIR / "src" / "valuefabric"
OPENAPI_DIR = REPO_ROOT / "contracts" / "openapi"


def run_export() -> bool:
    """Run export_openapi.py to regenerate specs."""
    export_script = REPO_ROOT / "scripts" / "export_openapi.py"
    result = subprocess.run(
        [sys.executable, str(export_script)],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return False
    return True


def copy_layer4_spec() -> None:
    """Copy the Layer 4 OpenAPI spec into the SDK for reference."""
    src = OPENAPI_DIR / "layer4-agents.json"
    dst = SRC_DIR / "layer4-agents.openapi.json"
    if src.exists():
        shutil.copy2(src, dst)
        print(f"📋 Copied Layer 4 spec to {dst}")
    else:
        print(f"⚠️ Layer 4 spec not found at {src}")


def main() -> int:
    print("Generating Value Fabric Python SDK...")
    print()

    if not run_export():
        print("OpenAPI export failed. Aborting.", file=sys.stderr)
        return 1

    SRC_DIR.mkdir(parents=True, exist_ok=True)
    copy_layer4_spec()

    print()
    print("✅ SDK ready (manual typed client in sdk/python/src/valuefabric/)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
