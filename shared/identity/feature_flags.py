"""Feature flag utilities."""

from __future__ import annotations

import logging
from typing import Any, Callable
from uuid import UUID

logger = logging.getLogger(__name__)

# In-memory store for feature flags
_feature_flags: dict[str, bool] = {}
_feature_flag_lookup: Callable[[str, UUID | None], bool] | None = None


def init_feature_flags(flags: dict[str, bool]) -> None:
    """Initialize feature flags.

    Args:
        flags: Dictionary of flag name to enabled status
    """
    global _feature_flags
    _feature_flags = dict(flags)
    logger.info(f"Initialized {len(flags)} feature flags")


def is_enabled(flag_name: str, tenant_id: UUID | None = None) -> bool:
    """Check if a feature flag is enabled.

    Args:
        flag_name: Name of the feature flag
        tenant_id: Optional tenant ID for tenant-specific flags

    Returns:
        True if flag is enabled
    """
    # Check custom lookup first
    if _feature_flag_lookup is not None:
        try:
            return _feature_flag_lookup(flag_name, tenant_id)
        except Exception as e:
            logger.warning(f"Feature flag lookup failed: {e}")

    # Fall back to global flags
    return _feature_flags.get(flag_name, False)


def register_feature_flag_lookup(
    lookup: Callable[[str, UUID | None], bool]
) -> None:
    """Register a custom lookup function for feature flags.

    Args:
        lookup: Function that takes flag name and tenant_id, returns bool
    """
    global _feature_flag_lookup
    _feature_flag_lookup = lookup
    logger.info("Custom feature flag lookup registered")
