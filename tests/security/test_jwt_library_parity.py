"""JWT library parity contract test.

Detects silent drift between the two JWT libraries used in this codebase:
  - packages/shared (PyJWT via value_fabric.shared.identity.jwt)
  - services/api    (python-jose via jose.jwt directly)

Both libraries must accept tokens produced by the other when using the same
secret, algorithm, issuer, and audience. This test does NOT migrate either
library — it acts as a drift detector so any future incompatibility is caught
at test time rather than at runtime.

Design note: ``services/api``'s ``decode_token`` wraps ``get_settings()`` which
is cached at import time and cannot be patched via ``os.environ`` after the
module is loaded. The tests therefore call ``jose.jwt.decode`` directly with
the shared test secret, which is the correct level of abstraction for a
cross-library parity test — we are testing that the two JWT libraries produce
and consume compatible token formats, not that the services/api settings
plumbing works.

Shared configuration used across all tests:
  - Algorithm: HS256
  - Secret:    32-byte test secret (satisfies both libraries' minimum length)
  - Issuer:    value-fabric-internal
  - Audience:  value-fabric-services
  - tenant_id: a valid UUID (required by decode_jwt)
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from uuid import UUID

import pytest

# ---------------------------------------------------------------------------
# Shared test configuration
# ---------------------------------------------------------------------------

_SECRET = "parity-test-secret-32-bytes-long!!"
_ISSUER = "value-fabric-internal"
_AUDIENCE = "value-fabric-services"
_ALGORITHM = "HS256"
_TENANT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_USER_ID = "parity-test-user-001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pyjwt_token(*, expires_in: int = 600) -> str:
    """Encode a token using PyJWT directly with the shared test secret."""
    import jwt as pyjwt

    now = int(time.time())
    return pyjwt.encode(
        {
            "sub": _USER_ID,
            "tenant_id": _TENANT_ID,
            "roles": ["analyst"],
            "iss": _ISSUER,
            "aud": _AUDIENCE,
            "iat": now,
            "exp": now + expires_in,
        },
        _SECRET,
        algorithm=_ALGORITHM,
    )


def _make_jose_token(*, expires_in: int = 600) -> str:
    """Encode a token using python-jose directly with the shared test secret."""
    from jose import jwt as jose_jwt

    now = int(time.time())
    return jose_jwt.encode(
        {
            "sub": _USER_ID,
            "tenant_id": _TENANT_ID,
            "roles": ["analyst"],
            "iss": _ISSUER,
            "aud": _AUDIENCE,
            "iat": now,
            "nbf": now,
            "exp": now + expires_in,
        },
        _SECRET,
        algorithm=_ALGORITHM,
    )


# ---------------------------------------------------------------------------
# Cross-library acceptance tests
# ---------------------------------------------------------------------------


def test_pyjwt_token_accepted_by_jose():
    """Token encoded by PyJWT is decoded correctly by python-jose."""
    from jose import jwt as jose_jwt

    token = _make_pyjwt_token()
    payload = jose_jwt.decode(
        token, _SECRET, algorithms=[_ALGORITHM],
        audience=_AUDIENCE, issuer=_ISSUER,
    )

    assert payload["sub"] == _USER_ID
    assert payload["tenant_id"] == _TENANT_ID
    assert payload["iss"] == _ISSUER
    assert payload["aud"] == _AUDIENCE


def test_jose_token_accepted_by_pyjwt():
    """Token encoded by python-jose is decoded correctly by PyJWT."""
    import jwt as pyjwt

    token = _make_jose_token()
    payload = pyjwt.decode(
        token, _SECRET, algorithms=[_ALGORITHM],
        audience=_AUDIENCE, issuer=_ISSUER,
    )

    assert payload["sub"] == _USER_ID
    assert payload["tenant_id"] == _TENANT_ID


def test_pyjwt_token_accepted_by_shared_decode_jwt():
    """Token encoded by PyJWT is accepted by the shared decode_jwt (PyJWT wrapper)."""
    from value_fabric.shared.identity.jwt import decode_jwt

    token = _make_pyjwt_token()

    # Patch env so decode_jwt uses our test secret
    old_secret = os.environ.get("JWT_SECRET")
    old_issuer = os.environ.get("JWT_ISSUER")
    old_audience = os.environ.get("JWT_AUDIENCE")
    try:
        os.environ["JWT_SECRET"] = _SECRET
        os.environ["JWT_ISSUER"] = _ISSUER
        os.environ["JWT_AUDIENCE"] = _AUDIENCE
        os.environ["OIDC_ISSUER"] = ""
        os.environ["ALLOW_LEGACY_TEST_TENANT_IDS"] = "false"
        claims = decode_jwt(token)
    finally:
        for k, v in [("JWT_SECRET", old_secret), ("JWT_ISSUER", old_issuer),
                     ("JWT_AUDIENCE", old_audience)]:
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    assert claims is not None, "shared decode_jwt rejected a PyJWT-encoded token"
    assert claims.sub == _USER_ID
    assert str(claims.tenant_id) == _TENANT_ID


# ---------------------------------------------------------------------------
# Shared rejection tests — both libraries must reject the same bad tokens
# ---------------------------------------------------------------------------


def test_expired_token_rejected_by_pyjwt():
    """Expired token raises DecodeError/ExpiredSignatureError from PyJWT."""
    import jwt as pyjwt

    token = _make_pyjwt_token(expires_in=-60)

    with pytest.raises(pyjwt.ExpiredSignatureError):
        pyjwt.decode(token, _SECRET, algorithms=[_ALGORITHM],
                     audience=_AUDIENCE, issuer=_ISSUER)


def test_expired_token_rejected_by_jose():
    """Expired token raises ExpiredSignatureError from python-jose."""
    from jose import ExpiredSignatureError
    from jose import jwt as jose_jwt

    token = _make_jose_token(expires_in=-60)

    with pytest.raises(ExpiredSignatureError):
        jose_jwt.decode(token, _SECRET, algorithms=[_ALGORITHM],
                        audience=_AUDIENCE, issuer=_ISSUER)


def test_wrong_secret_rejected_by_pyjwt():
    """Token signed with a different secret is rejected by PyJWT."""
    import jwt as pyjwt

    token = _make_jose_token()  # signed with _SECRET

    with pytest.raises(pyjwt.InvalidSignatureError):
        pyjwt.decode(token, "completely-different-secret-32ch!!",
                     algorithms=[_ALGORITHM], audience=_AUDIENCE, issuer=_ISSUER)


def test_wrong_secret_rejected_by_jose():
    """Token signed with a different secret is rejected by python-jose."""
    from jose import JWTError
    from jose import jwt as jose_jwt

    token = _make_pyjwt_token()  # signed with _SECRET

    with pytest.raises(JWTError):
        jose_jwt.decode(token, "completely-different-secret-32ch!!",
                        algorithms=[_ALGORITHM], audience=_AUDIENCE, issuer=_ISSUER)
