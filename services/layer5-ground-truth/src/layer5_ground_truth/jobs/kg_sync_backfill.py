"""Dedicated runner for Layer 5 → Layer 3 Knowledge Graph sync backfill.

Use this module from cron, Kubernetes CronJob, or another scheduler.
Triggers sync of approved TruthObjects to the L3 Knowledge Graph.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

from ..database import close_db, get_session_factory
from ..services.truth_service import list_truth_objects

logger = structlog.get_logger()

L3_SYNC_BATCH_SIZE = int(os.getenv("L5_L3_SYNC_BATCH_SIZE", "50"))


async def run_once(*, dry_run: bool = False) -> dict[str, Any]:
    """Run one L3 KG sync backfill pass.

    Finds approved TruthObjects that have not been synced to L3
    and triggers the sync-kg endpoint for each batch.
    """
    session_factory = get_session_factory()
    synced = 0
    failed = 0

    async with session_factory() as db:
        # Find approved truths that need syncing
        truths = await list_truth_objects(
            db,
            status="approved",
            limit=L3_SYNC_BATCH_SIZE,
        )

        if not truths:
            logger.info("L3 backfill: no approved truths pending sync")
            return {
                "synced": 0,
                "failed": 0,
                "dry_run": dry_run,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        l3_sync_url = os.getenv("L5_L3_SYNC_URL", "http://layer5-ground-truth:8005/api/v1/truths/sync-kg")

        for truth in truths:
            if dry_run:
                logger.info("L3 backfill dry-run: would sync truth %s", truth.id)
                synced += 1
                continue

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        l3_sync_url,
                        json={"truth_object_ids": [str(truth.id)]},
                        headers={"Content-Type": "application/json"},
                    )
                    response.raise_for_status()
                    synced += 1
                    logger.info("L3 backfill: synced truth %s", truth.id)
            except Exception as exc:
                failed += 1
                logger.warning("L3 backfill: failed to sync truth %s: %s", truth.id, exc)

    return {
        "synced": synced,
        "failed": failed,
        "dry_run": dry_run,
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def _async_main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    try:
        result = await run_once()
        logger.info(
            "L3 KG backfill complete: synced=%d failed=%d",
            result.get("synced", 0),
            result.get("failed", 0),
        )
        return 0
    finally:
        await close_db()


def main() -> None:
    """CLI entrypoint for schedulers."""
    raise SystemExit(asyncio.run(_async_main()))
