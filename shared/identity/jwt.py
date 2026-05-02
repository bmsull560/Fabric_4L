"""JWT encoding and decoding utilities with asymmetric key support.

SECURITY: Migrated from HS256 (symmetric) to RS256 (asymmetric) to reduce
blast radius and enable proper key rotation. Backward compatible during
transition period - accepts both HS256 and RS256 tokens.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_EXPIRATION_HOURS = 24

# Algorithm selection - prefer RS256 (asymmetric), fallback to HS256 for migration
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")
ALLOWED_ALGORITHMS = ["RS256", "HS256"]  # Accept both during migration

# Symmetric secret (HS256) - deprecated but supported for migration
JWT_SECRET = os.environ.get("JWT_SECRET")

# Asymmetric keys (RS256) - preferred for production
JWT_PRIVATE_KEY_PATH = os.getenv("JWT_PRIVATE_KEY_PATH", "/secrets/jwt-private.pem")
JWT_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH", "/secrets/jwt-public.pem")

# Lazy-loaded key cache
_signing_key: bytes | None = None
_verification_keys: list[bytes] = []


def _load_private_key() -> bytes:
    """Load RSA private key for signing."""
    global _signing_key
    if _signing_key is not None:
        return _signing_key
    
    if JWT_ALGORITHM == "RS256":
        try:
            with open(JWT_PRIVATE_KEY_PATH, "rb") as f:
                _signing_key = f.read()
            return _signing_key
        except FileNotFoundError:
            raise RuntimeError(
                f"RS256 private key not found at {JWT_PRIVATE_KEY_PATH}. "
                "Generate keys with: openssl genrsa -out jwt-private.pem 2048 && "
                "openssl rsa -in jwt-private.pem -pubout -out jwt-public.pem"
            )
    else:
        # HS256 mode - use shared secret
        if not JWT_SECRET:
            raise RuntimeError(
                "JWT_SECRET required for HS256. Consider migrating to RS256 "
                "for better security and key rotation support."
            )
        _signing_key = JWT_SECRET.encode("utf-8")
        return _signing_key


def _load_public_keys() -> list[bytes]:
    """Load RSA public keys for verification (supports rotation)."""
    global _verification_keys
    if _verification_keys:
        return _verification_keys
    
    keys = []
    
    # Load RS256 public key
    try:
        with open(JWT_PUBLIC_KEY_PATH, "rb") as f:
            keys.append(f.read())
    except FileNotFoundError:
        logger.warning(f"RS256 public key not found at {JWT_PUBLIC_KEY_PATH}")
    
    # Also load legacy secret for HS256 verification during migration
    if JWT_SECRET:
        keys.append(JWT_SECRET.encode("utf-8"))
    
    if not keys:
        raise RuntimeError(
            "No JWT verification keys available. "
            "Set JWT_PUBLIC_KEY_PATH (RS256) or JWT_SECRET (HS256)."
        )
    
    _verification_keys = keys
    return _verification_keys


def encode_jwt(
    payload: dict[str, Any],
    secret: str | None = None,
    algorithm: str | None = None,
    expiration_hours: int = JWT_EXPIRATION_HOURS,
) -> str:
    """Encode payload to JWT token.

    SECURITY: Uses RS256 (asymmetric) by default for production.
    HS256 (symmetric) supported for backward compatibility during migration.

    Args:
        payload: Data to encode
        secret: Deprecated - use key files for RS256
        algorithm: JWT algorithm (defaults to JWT_ALGORITHM env var, prefers RS256)
        expiration_hours: Token expiration time

    Returns:
        JWT token string
    """
    alg = algorithm or JWT_ALGORITHM
    
    # Add expiration
    exp = datetime.now(UTC) + timedelta(hours=expiration_hours)
    payload_with_exp = {**payload, "exp": exp}
    
    # Add key ID header for rotation support
    headers = {"kid": "current"} if alg == "RS256" else {}

    if alg == "RS256":
        signing_key = _load_private_key()
        return jwt.encode(payload_with_exp, signing_key, algorithm=alg, headers=headers)
    else:
        # HS256 fallback
        key = (secret or JWT_SECRET or "").encode("utf-8")
        if not key:
            raise RuntimeError("JWT_SECRET required for HS256 token encoding")
        return jwt.encode(payload_with_exp, key, algorithm=alg)


def decode_jwt(
    token: str,
    secret: str | None = None,
    algorithm: str | None = None,
) -> dict[str, Any] | None:
    """Decode JWT token with algorithm flexibility.

    SECURITY: Accepts both RS256 (asymmetric) and HS256 (symmetric) during
    migration period. Logs warnings for legacy HS256 tokens to track migration.

    Args:
        token: JWT token string
        secret: Deprecated - public keys used for RS256 verification
        algorithm: Optional specific algorithm to require

    Returns:
        Decoded payload or None if invalid/expired
    """
    try:
        # Determine which algorithms to allow
        if algorithm:
            allowed = [algorithm]
        else:
            allowed = ALLOWED_ALGORITHMS
        
        # Try each verification key
        keys_to_try = []
        
        if secret:
            # Legacy HS256 path
            keys_to_try.append(secret.encode("utf-8"))
        else:
            # Standard path - load keys from files/secrets
            keys_to_try = _load_public_keys()
        
        last_error = None
        for key in keys_to_try:
            try:
                decoded = jwt.decode(token, key, algorithms=allowed)
                
                # Log migration warning for HS256 tokens
                if decoded.get("alg") == "HS256" or algorithm == "HS256":
                    logger.debug("Legacy HS256 token accepted - consider reissuing as RS256")
                
                return decoded
            except jwt.InvalidTokenError as e:
                last_error = e
                continue
        
        # All keys failed
        if last_error:
            raise last_error
        return None
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"JWT decode error: {e}")
        return None
