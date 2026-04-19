"""JWT encoding and decoding utilities."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

logger = logging.getLogger(__name__)

# Get secret from environment - fail closed if not set
JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET environment variable is required. "
        "Set a strong random secret (32+ bytes)."
    )
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def encode_jwt(
    payload: dict[str, Any],
    secret: str | None = None,
    algorithm: str = JWT_ALGORITHM,
    expiration_hours: int = JWT_EXPIRATION_HOURS,
) -> str:
    """Encode payload to JWT token.

    Args:
        payload: Data to encode
        secret: JWT secret (defaults to JWT_SECRET env var)
        algorithm: JWT algorithm
        expiration_hours: Token expiration time

    Returns:
        JWT token string
    """
    secret = secret or JWT_SECRET

    # Add expiration
    exp = datetime.now(UTC) + timedelta(hours=expiration_hours)
    payload_with_exp = {**payload, "exp": exp}

    return jwt.encode(payload_with_exp, secret, algorithm=algorithm)


def decode_jwt(
    token: str,
    secret: str | None = None,
    algorithm: str = JWT_ALGORITHM,
) -> dict[str, Any] | None:
    """Decode JWT token.

    Args:
        token: JWT token string
        secret: JWT secret (defaults to JWT_SECRET env var)
        algorithm: JWT algorithm

    Returns:
        Decoded payload or None if invalid
    """
    secret = secret or JWT_SECRET

    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
