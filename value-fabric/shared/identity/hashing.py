"""API key hashing and verification helpers.

Design (per review feedback):
- HMAC-SHA256 with a server-side secret (``API_KEY_HMAC_SECRET`` env var)
  for API key hashing — industry standard (Stripe, GitHub, AWS use this).
- bcrypt is intentionally NOT used here; bcrypt (~100ms/hash) kills throughput
  at scale. HMAC-SHA256 is ~1µs and still cryptographically safe because the
  server secret acts as a pepper.
- bcrypt is only appropriate for *user passwords*, which are in
  ``layer4-agents/src/tenants/models/user.py``.
"""

from __future__ import annotations

import hmac
import hashlib
import os
import secrets
from typing import Optional

_KEY_PREFIX = "vf_"
_KEY_BYTE_LENGTH = 32  # 256 bits of entropy → 43 base64url chars


def _get_hmac_secret() -> bytes:
    """Return the server-side HMAC secret from the environment."""
    secret = os.getenv("API_KEY_HMAC_SECRET", "")
    if not secret:
        import logging
        logging.getLogger(__name__).warning(
            "API_KEY_HMAC_SECRET is not set — using empty string. "
            "Set a strong secret in production."
        )
    return secret.encode("utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_api_key() -> str:
    """Generate a new random API key.

    Returns a URL-safe string with the ``vf_`` prefix, e.g.::

        vf_8xKj3nFqZ0...

    The prefix makes it easy for scanners (e.g. GitHub secret scanning) to
    identify leaked Value Fabric keys.
    """
    random_part = secrets.token_urlsafe(_KEY_BYTE_LENGTH)
    return f"{_KEY_PREFIX}{random_part}"


def hash_api_key(raw_key: str) -> str:
    """Return the HMAC-SHA256 hex digest for ``raw_key``.

    This value is stored in the database; the raw key is never stored.
    """
    secret = _get_hmac_secret()
    return hmac.new(secret, raw_key.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """Constant-time comparison of ``hash_api_key(raw_key)`` vs ``stored_hash``.

    Uses :func:`hmac.compare_digest` to prevent timing attacks.
    """
    expected = hash_api_key(raw_key)
    return hmac.compare_digest(expected, stored_hash)


def extract_key_prefix(raw_key: str, prefix_length: int = 12) -> str:
    """Return the first ``prefix_length`` characters for display purposes.

    The prefix is shown in the admin UI so admins can identify which key was
    used without exposing the full secret.
    """
    return raw_key[:prefix_length]
