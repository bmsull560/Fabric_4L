#!/usr/bin/env python3
"""Validate build/promotion workflow artifact contract compatibility."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_KEYS = {"layer", "image_digest", "published_tag", "source_commit_sha"}
BUILD_MARKER = "build-metadata-${{ matrix.layer }}"
PROMOTION_MARKER = "build-metadata-*"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build-workflow", type=Path, required=True)
    p.add_argument("--promotion-workflow", type=Path, required=True)
    p.add_argument("--metadata-dir", type=Path)
    return p.parse_args()


def fail(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    args = parse_args()
    build_text = args.build_workflow.read_text(encoding="utf-8")
    promo_text = args.promotion_workflow.read_text(encoding="utf-8")

    if BUILD_MARKER not in build_text:
        fail(f"Missing build artifact marker in {args.build_workflow}: {BUILD_MARKER}")
    if PROMOTION_MARKER not in promo_text:
        fail(f"Missing promotion artifact pattern in {args.promotion_workflow}: {PROMOTION_MARKER}")

    if args.metadata_dir is not None:
        files = sorted(args.metadata_dir.glob("*.json"))
        if not files:
            fail(f"No metadata JSON files found in {args.metadata_dir}")
        for path in files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            missing = REQUIRED_KEYS - set(payload.keys())
            if missing:
                fail(f"{path} missing keys: {sorted(missing)}")
            if not str(payload["image_digest"]).startswith("sha256:"):
                fail(f"{path} has invalid image_digest {payload['image_digest']!r}")
            if not str(payload["published_tag"]).startswith("sha-"):
                fail(f"{path} has invalid published_tag {payload['published_tag']!r}")
            if len(str(payload["source_commit_sha"])) != 40:
                fail(f"{path} has invalid source_commit_sha length")

    print("Build/promotion artifact schema contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
