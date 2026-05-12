"""API key generation and HMAC hashing helpers."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets


def generate_api_key() -> str:
    """Generate a tenant API key value returned only at creation time."""

    return f"vf_live_{secrets.token_urlsafe(32)}"


def extract_key_prefix(api_key: str) -> str:
    """Return a non-secret prefix suitable for UI display and lookup metadata."""

    return api_key[:12]


def hash_api_key(api_key: str) -> str:
    """Hash an API key with a server-side HMAC secret."""

    secret = _hmac_secret()
    digest = hmac.new(secret.encode("utf-8"), api_key.encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()


def verify_api_key(api_key: str, expected_hash: str) -> bool:
    """Constant-time verification helper for stored API key hashes."""

    return hmac.compare_digest(hash_api_key(api_key), expected_hash)


def _hmac_secret() -> str:
    secret = os.getenv("API_KEY_HMAC_SECRET") or os.getenv("SERVICE_AUTH_SECRET")
    if secret:
        return secret
    if os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).lower() in {"production", "prod"}:
        raise RuntimeError("API_KEY_HMAC_SECRET is required in production")
    return "development-only-api-key-hmac-secret"
