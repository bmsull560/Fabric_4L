"""API key hashing and generation utilities."""

from __future__ import annotations

import hashlib
import logging
import secrets

logger = logging.getLogger(__name__)

# Prefix for API keys
API_KEY_PREFIX = "vf_"
API_KEY_LENGTH = 48  # Total length including prefix


def generate_api_key() -> str:
    """Generate a new API key with prefix.

    Returns:
        API key string (e.g., "vf_a1b2c3d4e5f6...")
    """
    # Generate 32 bytes of randomness = 64 hex chars
    random_part = secrets.token_hex(32)
    return f"{API_KEY_PREFIX}{random_part}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage.

    Args:
        api_key: The plain API key

    Returns:
        SHA-256 hash of the key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def extract_key_prefix(api_key: str) -> str:
    """Extract prefix from API key for indexing.

    Args:
        api_key: The API key

    Returns:
        First 8 characters after prefix
    """
    if api_key.startswith(API_KEY_PREFIX):
        return api_key[len(API_KEY_PREFIX) : len(API_KEY_PREFIX) + 8]
    return api_key[:8]


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash.

    Args:
        api_key: Plain API key
        hashed_key: Stored hash

    Returns:
        True if key matches hash
    """
    return hash_api_key(api_key) == hashed_key
