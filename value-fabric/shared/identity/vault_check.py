"""Async Vault health and secret-access verification helpers."""

import os
from typing import List

import httpx


# In-memory cache for Vault secrets to avoid repeated lookups
_vault_secret_cache: dict[str, tuple[str, float]] = {}
_VAULT_CACHE_TTL_SECONDS = 300  # 5 minutes


def _parse_vault_ref(ref: str) -> tuple[str, str] | None:
    """Parse a vault reference like 'vault:secret/data/my-secret' into (path, key).

    Supports formats:
    - vault:secret/data/path
    - vault:secret/data/path#key
    - vault:secret/data/path.field
    """
    if not ref.startswith("vault:"):
        return None

    path_part = ref[6:]  # Remove 'vault:' prefix

    # Check for field extraction syntax
    if "#" in path_part:
        path, key = path_part.split("#", 1)
    elif "." in path_part and "/" not in path_part.split(".")[-1]:
        # Last dot separates path from field if no slash after it
        path, key = path_part.rsplit(".", 1)
    else:
        path = path_part
        key = "value"  # Default key

    return (path.lstrip("/"), key)


async def resolve_vault_secret(ref: str) -> str | None:
    """Resolve a Vault secret reference to its value.

    Args:
        ref: Vault reference like 'vault:secret/data/my-secret#api_key'

    Returns:
        The secret value or None if resolution fails.
    """
    parsed = _parse_vault_ref(ref)
    if parsed is None:
        return None

    path, key = parsed
    cache_key = f"{path}#{key}"

    # Check cache
    cached = _vault_secret_cache.get(cache_key)
    if cached:
        value, cached_at = cached
        import time
        if time.time() - cached_at < _VAULT_CACHE_TTL_SECONDS:
            return value

    vault_addr = os.getenv("VAULT_ADDR", "")
    token = os.getenv("VAULT_TOKEN", "")

    if not vault_addr or not token:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"X-Vault-Token": token}
            url = f"{vault_addr.rstrip('/')}/v1/{path}"
            resp = await client.get(url, headers=headers)

            if resp.status_code != 200:
                return None

            data = resp.json()
            secret_data = data.get("data", {}).get("data", {})
            value = secret_data.get(key)

            if value:
                import time
                _vault_secret_cache[cache_key] = (value, time.time())

            return value
    except Exception:
        return None


def clear_vault_cache() -> None:
    """Clear the Vault secret cache. Useful for testing."""
    _vault_secret_cache.clear()


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
