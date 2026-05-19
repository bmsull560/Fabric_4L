"""Startup dependency verifier for Layer 2 extraction."""

from __future__ import annotations

import importlib.util
import logging
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class DependencyRule:
    """Rule for a startup dependency."""

    module: str
    required_in_prod: bool
    remediation: str


def verify_startup_dependencies(
    rules: list[DependencyRule] | None = None,
    environment: str = "development",
) -> None:
    """Verify startup dependencies and fail closed in production."""
    if rules is None:
        rules = []
    for rule in rules:
        spec = importlib.util.find_spec(rule.module)
        if spec is None:
            if environment == "production" and rule.required_in_prod:
                raise RuntimeError(
                    f"Required dependency '{rule.module}' is missing in production. "
                    f"Remediation: {rule.remediation}"
                )
            level = logging.ERROR if rule.required_in_prod else logging.WARNING
            logger.log(level, f"Dependency '{rule.module}' is missing. Remediation: {rule.remediation}")


def verify_layer2_startup_dependencies(environment: str = "development") -> None:
    """Verify Layer 2 startup dependencies using the built-in catalog."""
    rules = [
        DependencyRule("redis", required_in_prod=True, remediation="pip install redis"),
        DependencyRule("asyncpg", required_in_prod=True, remediation="pip install asyncpg"),
    ]
    verify_startup_dependencies(rules, environment=environment)
