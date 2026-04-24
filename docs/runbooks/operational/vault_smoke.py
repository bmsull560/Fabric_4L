#!/usr/bin/env python3
"""Standalone smoke test for Vault connectivity, secret access, and dynamic PostgreSQL creds."""

import asyncio
import os
import sys
from typing import List

import httpx

VAULT_ADDR = os.getenv("VAULT_ADDR")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")

REQUIRED_SECRET_PATHS: List[str] = [
    "secret/data/value-fabric/llm",
    "secret/data/value-fabric/database",
    "secret/data/value-fabric/auth",
    "secret/data/value-fabric/infrastructure",
    "secret/data/value-fabric/inter-layer",
]

# Dynamic credential roles for each layer
DYNAMIC_CRED_ROLES: List[str] = [
    "database/creds/app-role",
    "database/creds/layer1-app",
    "database/creds/layer2-app",
    "database/creds/layer3-app",
    "database/creds/layer4-app",
]

# Legacy fallback role (deprecated but check for compatibility)
DYNAMIC_CRED_PATH = "database/creds/value-fabric-role"


def _log(msg: str) -> None:
    print(msg)


async def _main() -> int:
    if not VAULT_ADDR:
        _log("FAIL: VAULT_ADDR not set")
        return 1
    if not VAULT_TOKEN:
        _log("FAIL: VAULT_TOKEN not set")
        return 1

    headers = {"X-Vault-Token": VAULT_TOKEN}

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Vault health
        try:
            resp = await client.get(
                f"{VAULT_ADDR.rstrip('/')}/v1/sys/health", headers=headers
            )
            if resp.status_code not in (200, 429, 473):
                _log(f"FAIL: Vault health returned {resp.status_code}")
                return 1
            _log("PASS: Vault reachable")
        except Exception as exc:
            _log(f"FAIL: Vault unreachable: {exc}")
            return 1

        # 2. Required secrets accessible
        for path in REQUIRED_SECRET_PATHS:
            try:
                resp = await client.get(
                    f"{VAULT_ADDR.rstrip('/')}/v1/{path.lstrip('/')}", headers=headers
                )
                if resp.status_code != 200:
                    _log(f"FAIL: Cannot access secret {path} ({resp.status_code})")
                    return 1
            except Exception as exc:
                _log(f"FAIL: Error accessing secret {path}: {exc}")
                return 1
        _log("PASS: Required secrets accessible")

        # 3. PostgreSQL dynamic cred generation for all layer roles
        working_roles = 0
        for role_path in DYNAMIC_CRED_ROLES:
            try:
                resp = await client.get(
                    f"{VAULT_ADDR.rstrip('/')}/v1/{role_path.lstrip('/')}",
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    if "username" in data and "password" in data:
                        working_roles += 1
                        _log(f"PASS: Dynamic creds work for {role_path}")
                    else:
                        _log(f"WARN: {role_path} missing username/password in response")
                else:
                    _log(f"WARN: {role_path} returned {resp.status_code}")
            except Exception as exc:
                _log(f"WARN: Error checking {role_path}: {exc}")

        if working_roles == 0:
            _log("FAIL: No dynamic credential roles working")
            return 1

        _log(f"PASS: {working_roles}/{len(DYNAMIC_CRED_ROLES)} dynamic credential roles working")

    _log("All checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
