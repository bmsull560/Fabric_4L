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
]

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

        # 3. PostgreSQL dynamic cred generation
        try:
            resp = await client.get(
                f"{VAULT_ADDR.rstrip('/')}/v1/{DYNAMIC_CRED_PATH.lstrip('/')}",
                headers=headers,
            )
            if resp.status_code != 200:
                _log(f"FAIL: Dynamic cred generation returned {resp.status_code}")
                return 1
            data = resp.json().get("data", {})
            if "username" not in data or "password" not in data:
                _log("FAIL: Dynamic cred response missing username/password")
                return 1
            _log("PASS: PostgreSQL dynamic cred generation works")
        except Exception as exc:
            _log(f"FAIL: Dynamic cred generation error: {exc}")
            return 1

    _log("All checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
