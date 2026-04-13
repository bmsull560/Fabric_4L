"""CLI script to check the evaluation gate for a model version.

Usage:
    python scripts/ci_eval_gate.py --model-version-id <uuid> --min-score 0.85

Exit codes:
    0 — gate passed
    1 — gate failed or error
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from uuid import UUID


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CI evaluation gate checker")
    parser.add_argument(
        "--model-version-id",
        required=True,
        help="UUID of the model version to evaluate",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.85,
        help="Minimum evaluation score required (default: 0.85)",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()

    try:
        model_version_id = UUID(args.model_version_id)
    except ValueError:
        print("Invalid model-version-id: must be a valid UUID", file=sys.stderr)
        return 1

    import os

    # Ensure layer4-agents src is on path
    layer4_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "value-fabric", "layer4-agents")
    if layer4_src not in sys.path:
        sys.path.insert(0, layer4_src)

    from src.database import db_session
    from src.registry.eval_gate import check_eval_gate

    async with db_session() as db:
        passed = await check_eval_gate(db, model_version_id, min_score=args.min_score)

    if passed:
        print(f"Evaluation gate PASSED for {model_version_id} (min_score={args.min_score})")
        return 0

    print(f"Evaluation gate FAILED for {model_version_id} (min_score={args.min_score})", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
