"""Async Vault health and secret-access verification helpers."""

import os
from typing import List

import httpx


async def check_vault_health(vault_addr: str) -> bool:
    """Return True if Vault is reachable and unsealed (or standby)."""
    token = os.getenv("VAULT_TOKEN", "")
    headers = {"X-Vault-Token": token} if token else {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{vault_addr.rstrip('/')}/v1/sys/health", headers=headers
            )
            # 200 = active, 429 = standby, 473 = recovery replication secondary
            return resp.status_code in (200, 429, 473)
    except Exception:
        return False


async def verify_secret_access(vault_addr: str, paths: List[str]) -> bool:
    """Return True if Vault token can read every path in `paths`."""
    token = os.getenv("VAULT_TOKEN", "")
    if not token:
        return False
    headers = {"X-Vault-Token": token}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for path in paths:
                url = f"{vault_addr.rstrip('/')}/v1/{path.lstrip('/')}"
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return False
            return True
    except Exception:
        return False
