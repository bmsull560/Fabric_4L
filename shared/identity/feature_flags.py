"""Feature flag utilities with user-based bucketing for gradual rollouts.

Implements stable user bucketing using hash(flag_key + tenant_id + user_id) % 100 < rollout_pct
for consistent user experiences across sessions.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Callable
from uuid import UUID

logger = logging.getLogger(__name__)

# In-memory store for feature flags (fallback)
_feature_flags: dict[str, bool] = {}
# Callback to lookup flag data from database (returns dict with 'enabled', 'rollout_percentage')
_feature_flag_lookup: Callable[[str, UUID | None], dict[str, Any] | None] | None = None


def _compute_user_bucket(flag_key: str, tenant_id: UUID | None, user_id: str | None) -> int:
    """Compute stable bucket (0-99) for user-based rollout.

    Uses SHA-256 hash of flag_key + tenant_id + user_id for consistent
    bucketing across sessions. Same user always gets same bucket for
    same flag, enabling gradual rollouts without user experience jumps.

    Args:
        flag_key: Feature flag identifier
        tenant_id: Tenant UUID or None
        user_id: User identifier string or None

    Returns:
        Bucket value 0-99
    """
    # Build stable key for hashing
    parts = [flag_key]
    if tenant_id is not None:
        parts.append(str(tenant_id))
    # For non-user traffic, use tenant_id as actor key if available
    if user_id is not None:
        parts.append(user_id)
    elif tenant_id is not None:
        parts.append(str(tenant_id))  # Fallback to tenant for non-user traffic
    else:
        parts.append("global")  # Global fallback

    hash_input = "|".join(parts)
    hash_bytes = hashlib.sha256(hash_input.encode()).digest()
    # Use first 4 bytes for bucket (0-99)
    bucket = int.from_bytes(hash_bytes[:4], byteorder="big") % 100
    return bucket


def _should_enable_for_user(flag_data: dict[str, Any], flag_key: str, tenant_id: UUID | None, user_id: str | None) -> bool:
    """Determine if flag should be enabled for specific user based on rollout.

    Args:
        flag_data: Dict with 'enabled' (bool) and 'rollout_percentage' (int)
        flag_key: Feature flag identifier
        tenant_id: Tenant UUID
        user_id: User identifier

    Returns:
        True if flag is enabled for this user
    """
    # If globally disabled, never enable
    if not flag_data.get("enabled", False):
        return False

    rollout_pct = flag_data.get("rollout_percentage", 0)

    # If fully rolled out (100%), enable for all
    if rollout_pct >= 100:
        return True

    # If no rollout (0%), only enable if specifically targeted (not implemented yet)
    if rollout_pct <= 0:
        return False

    # Compute user bucket and check against rollout percentage
    bucket = _compute_user_bucket(flag_key, tenant_id, user_id)
    return bucket < rollout_pct


def init_feature_flags(flags: dict[str, bool]) -> None:
    """Initialize feature flags (fallback for non-DB deployments).

    Args:
        flags: Dictionary of flag name to enabled status
    """
    global _feature_flags
    _feature_flags = {k: {"enabled": v, "rollout_percentage": 100 if v else 0} for k, v in flags.items()}
    logger.info(f"Initialized {len(flags)} feature flags")


def is_enabled(
    flag_key: str,
    tenant_id: UUID | None = None,
    user_id: str | None = None,
) -> bool:
    """Check if a feature flag is enabled for the given context.

    Implements user-based bucketing for gradual rollouts:
    - Uses stable hash of (flag_key + tenant_id + user_id) % 100 < rollout_pct
    - Consistent experience for same user across sessions
    - For non-user traffic, falls back to tenant_id as actor key

    Args:
        flag_key: Name of the feature flag
        tenant_id: Optional tenant ID for tenant-specific flags
        user_id: Optional user ID for user-scoped bucketing

    Returns:
        True if flag is enabled for this user/tenant context
    """
    # Check custom lookup first (database-backed flags)
    if _feature_flag_lookup is not None:
        try:
            flag_data = _feature_flag_lookup(flag_key, tenant_id)
            if flag_data is not None:
                return _should_enable_for_user(flag_data, flag_key, tenant_id, user_id)
        except Exception as e:
            logger.warning(f"Feature flag lookup failed for {flag_key}: {e}")

    # Fall back to global flags (in-memory)
    flag_data = _feature_flags.get(flag_key)
    if flag_data is not None:
        return _should_enable_for_user(flag_data, flag_key, tenant_id, user_id)

    return False


def register_feature_flag_lookup(
    lookup: Callable[[str, UUID | None], dict[str, Any] | None]
) -> None:
    """Register a custom lookup function for feature flags.

    Args:
        lookup: Function that takes (flag_name, tenant_id) and returns
                dict with 'enabled' (bool) and 'rollout_percentage' (int)
                or None if flag not found
    """
    global _feature_flag_lookup
    _feature_flag_lookup = lookup
    logger.info("Custom feature flag lookup registered")
