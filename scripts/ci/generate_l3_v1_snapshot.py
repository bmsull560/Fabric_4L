"""Generate the Layer 3 V1 API snapshot (DOC-ARCH-010).

Copies the current Layer 3 OpenAPI contract to ``docs/api/v1_snapshot.yaml``
and stamps it with snapshot metadata.  Run this once before the v2 cutover
(ARCH-L3-011) to lock the backward-compatibility baseline.

Usage
-----
    python scripts/ci/generate_l3_v1_snapshot.py [--force]

    --force   Overwrite an existing snapshot (default: refuse if snapshot exists).

Exit codes
----------
    0  Snapshot written (or already up-to-date with --force).
    1  Snapshot already exists and --force was not passed.
    2  Source contract not found.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_CONTRACT = REPO_ROOT / "contracts/openapi/layer3-knowledge.json"
SNAPSHOT_PATH = REPO_ROOT / "docs/api/v1_snapshot.yaml"

_SNAPSHOT_DESCRIPTION = (
    "Locked snapshot of the Layer 3 Knowledge Graph API at the point of v2 router "
    "scaffolding (ARCH-L3-007 Part 1). Used by CI contract diffing to guarantee "
    "V2 routers maintain backward compatibility before full monolith removal (ARCH-L3-011).\n\n"
    "DO NOT EDIT MANUALLY. Re-generate with: python scripts/ci/generate_l3_v1_snapshot.py --force"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing snapshot.",
    )
    args = parser.parse_args()

    if not SOURCE_CONTRACT.exists():
        print(f"ERROR: Source contract not found: {SOURCE_CONTRACT}", file=sys.stderr)
        return 2

    if SNAPSHOT_PATH.exists() and not args.force:
        print(
            f"Snapshot already exists: {SNAPSHOT_PATH}\n"
            "Pass --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    with SOURCE_CONTRACT.open() as fh:
        spec = json.load(fh)

    spec["info"]["title"] = "Value Fabric Layer 3 - V1 API Snapshot"
    spec["info"]["description"] = _SNAPSHOT_DESCRIPTION
    spec["info"]["x-snapshot-date"] = str(date.today())
    spec["info"]["x-snapshot-ticket"] = "DOC-ARCH-010"
    spec["info"]["x-cutover-ticket"] = "ARCH-L3-011"

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SNAPSHOT_PATH.open("w") as fh:
        json.dump(spec, fh, indent=2)
        fh.write("\n")

    path_count = len(spec.get("paths", {}))
    print(f"Snapshot written: {SNAPSHOT_PATH} ({path_count} paths)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
