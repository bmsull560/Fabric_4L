"""Authentication mode inspection and startup validation utilities."""

from __future__ import annotations

import logging
import os

from value_fabric.shared.security.config import is_production_like_environment

logger = logging.getLogger(__name__)

_BYPASS_ACK_VALUE = "I_UNDERSTAND_RISK"


def _normalized_env() -> str:
    return (os.getenv("ENVIRONMENT", "production") or "production").strip().lower()


def is_dev_bypass_enabled() -> bool:
    return os.getenv("DEV_AUTH_BYPASS", "").strip().lower() == "true"


def is_dev_bypass_acknowledged() -> bool:
    return os.getenv("ALLOW_DEV_AUTH_BYPASS", "").strip() == _BYPASS_ACK_VALUE


def validate_dev_bypass_configuration() -> None:
    """Fail closed when dev-bypass toggles are unsafe."""
    if not is_dev_bypass_enabled():
        return

    environment = _normalized_env()
    if environment != "development":
        raise RuntimeError(
            "FATAL: DEV_AUTH_BYPASS=true is only permitted when ENVIRONMENT=development."
        )
    if not is_dev_bypass_acknowledged():
        raise RuntimeError(
            "FATAL: DEV_AUTH_BYPASS=true requires "
            "ALLOW_DEV_AUTH_BYPASS=I_UNDERSTAND_RISK."
        )


def assert_safe_jwt_and_bypass_configuration() -> None:
    """Refuse startup when production-like environments enable bypass toggles."""
    environment = _normalized_env()
    if is_production_like_environment(environment) and (
        is_dev_bypass_enabled() or is_dev_bypass_acknowledged()
    ):
        raise RuntimeError(
            "FATAL: Production-like environment cannot run with dev auth bypass toggles. "
            "Unset DEV_AUTH_BYPASS and ALLOW_DEV_AUTH_BYPASS."
        )


def log_auth_mode_report() -> None:
    """Log active/disabled auth sources for startup observability."""
    environment = _normalized_env()
    bypass_enabled = is_dev_bypass_enabled()
    bypass_ack = is_dev_bypass_acknowledged()

    active_sources = ["jwt_middleware"]
    if bypass_enabled:
        active_sources.append("dev_auth_bypass")

    disabled_sources: list[str] = []
    if not bypass_enabled:
        disabled_sources.append("dev_auth_bypass")
    if not bypass_ack:
        disabled_sources.append("dev_bypass_ack")
    disabled_sources.append("api_key_auth")

    logger.info(
        "Auth mode report: environment=%s active_sources=%s disabled_sources=%s",
        environment,
        ",".join(active_sources),
        ",".join(disabled_sources),
    )

