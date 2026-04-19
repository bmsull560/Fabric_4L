"""Vault health check utilities."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def check_vault_health(
    vault_url: str | None = None,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """Check HashiCorp Vault health status.

    Args:
        vault_url: Vault URL (defaults to VAULT_ADDR env var)
        timeout: Request timeout in seconds

    Returns:
        Health status dictionary
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
