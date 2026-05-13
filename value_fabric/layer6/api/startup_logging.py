from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any

LOGGER = logging.getLogger("layer6.startup")


def config_fingerprint(config: dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def emit_startup_metadata(*, service: str, version: str, build_sha: str, config: dict[str, Any]) -> None:
    LOGGER.info(
        "layer6_startup",
        extra={
            "service": service,
            "version": version,
            "build_sha": build_sha,
            "config_fingerprint": config_fingerprint(config),
        },
    )


def runtime_metadata_from_env() -> dict[str, str]:
    return {
        "service": os.getenv("LAYER6_SERVICE_NAME", "layer6-benchmarks"),
        "version": os.getenv("LAYER6_VERSION", "dev"),
        "build_sha": os.getenv("LAYER6_BUILD_SHA", "unknown"),
    }
