"""Vault health check utilities."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def get_vault_health(
    vault_url: str | None = None,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """Get detailed HashiCorp Vault health status.

    Use this for health endpoints and diagnostics that need full status details.
    For startup gates that only need a binary pass/fail, use is_vault_healthy().

    Args:
        vault_url: Vault URL (defaults to VAULT_ADDR env var)
        timeout: Request timeout in seconds

    Returns:
        Health status dictionary with keys:
        - status: "healthy", "degraded", or "unreachable"
        - initialized: bool (whether Vault is initialized)
        - sealed: bool (whether Vault is sealed)
        - standby: bool (whether Vault is in standby)
        - version: str (Vault version or "unknown")
        - error: str (error message if unreachable)
        - reachable: bool (whether Vault responded)
    """
    vault_url = vault_url or os.environ.get("VAULT_ADDR", "http://localhost:8200")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{vault_url}/v1/sys/health",
                timeout=timeout,
            )

            # Vault returns different status codes:
            # 200 = initialized, unsealed, active
            # 429 = unsealed, standby
            # 501 = not initialized
            # 503 = sealed

            data = response.json() if response.status_code != 503 else {}

            return {
                "status": "healthy" if response.status_code == 200 else "degraded",
                "initialized": data.get("initialized", False),
                "sealed": data.get("sealed", True),
                "standby": data.get("standby", False),
                "version": data.get("version", "unknown"),
            }

    except Exception as e:
        logger.warning(f"Vault health check failed: {e}")
        return {
            "status": "unreachable",
            "error": str(e),
            "reachable": False,
        }


async def is_vault_healthy(
    vault_url: str | None = None,
    timeout: float = 5.0,
) -> bool:
    """Check if Vault is healthy for startup gates.

    Returns True only if Vault returns HTTP 200 (initialized, unsealed, active).
    Returns False for any other status (standby, sealed, not initialized, unreachable).

    Use this for production startup gates that need a simple pass/fail check.
    For detailed diagnostics, use get_vault_health().

    Args:
        vault_url: Vault URL (defaults to VAULT_ADDR env var)
        timeout: Request timeout in seconds

    Returns:
        True if Vault is healthy and ready, False otherwise
    """
    health = await get_vault_health(vault_url, timeout)
    return health.get("status") == "healthy"


# Backward compatibility alias - deprecated, use is_vault_healthy() instead
async def check_vault_health(
    vault_url: str | None = None,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """Deprecated: Use get_vault_health() for detailed status or is_vault_healthy() for boolean checks."""
    return await get_vault_health(vault_url, timeout)
