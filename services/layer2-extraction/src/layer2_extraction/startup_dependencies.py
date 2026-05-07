from __future__ import annotations

import importlib.util
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)
PROD_ENVS = {"production", "prod", "staging", "stage"}


@dataclass(frozen=True)
class DependencySpec:
    module: str
    required_in_prod: bool
    remediation: str


DEPENDENCIES = (
    DependencySpec("psutil", required_in_prod=False, remediation="Install psutil to enable host health metrics in /health responses."),
    DependencySpec("redis", required_in_prod=True, remediation="Install redis-py and configure REDIS_URL for distributed rate limiting."),
)


def verify_startup_dependencies(*, environment: str | None = None) -> None:
    env = (environment or os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or os.getenv("LAYER2_ENV") or "development").strip().lower()
    prod_like = env in PROD_ENVS
    for dep in DEPENDENCIES:
        available = importlib.util.find_spec(dep.module) is not None
        if available:
            continue
        detail = f"missing module '{dep.module}'. Remediation: {dep.remediation}"
        if dep.required_in_prod and prod_like:
            logger.error("L2 startup dependency check failed in %s: %s", env, detail)
            raise RuntimeError(f"Required startup dependency unavailable in {env}: {detail}")
        logger.warning("L2 optional startup dependency unavailable in %s: %s", env, detail)
