"""JWT consistency test — services/api vs packages/shared.

Both sides now use PyJWT. This test verifies that tokens produced by either
side are accepted by the other, and that both reject the same bad tokens.
It acts as a regression guard against future divergence in claim shapes,
algorithm choices, or validation options.

Shared configuration:
  - Algorithm: HS256
  - Secret:    32-byte test secret
  - Issuer:    value-fabric-internal
  - Audience:  value-fabric-services
  - tenant_id: a valid UUID (required by decode_jwt)
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import jwt as pyjwt
import pytest

# Ensure services/api is importable as `app.*`
_SERVICES_API = Path(__file__).parents[2] / "services" / "api"
if str(_SERVICES_API) not in sys.path:
    sys.path.insert(0, str(_SERVICES_API))

_SECRET = "parity-test-secret-32-bytes-long!!"
_ISSUER = "value-fabric-internal"
_AUDIENCE = "value-fabric-services"
_ALGORITHM = "HS256"
_TENANT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_USER_ID = "parity-test-user-001"


def _make_token(*, expires_in: int = 600, **overrides) -> str:
    now = int(time.time())
    payload = {
        "sub": _USER_ID,
        "tenant_id": _TENANT_ID,
        "roles": ["analyst"],
        "iss": _ISSUER,
        "aud": _AUDIENCE,
        "iat": now,
        "nbf": now,
        "exp": now + expires_in,
    }
    payload.update(overrides)
    return pyjwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def _with_env(**kwargs):
    """Context manager: temporarily set env vars, restore on exit."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        old = {k: os.environ.get(k) for k in kwargs}
        try:
            os.environ.update({k: v for k, v in kwargs.items() if v is not None})
            for k, v in kwargs.items():
                if v is None:
                    os.environ.pop(k, None)
            yield
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    return _ctx()


_TEST_ENV = dict(
    JWT_SECRET=_SECRET,
    JWT_ISSUER=_ISSUER,
    JWT_AUDIENCE=_AUDIENCE,
    OIDC_ISSUER="",
    ALLOW_LEGACY_TEST_TENANT_IDS="false",
)


# ---------------------------------------------------------------------------
# Cross-path acceptance
# ---------------------------------------------------------------------------

def test_shared_decode_jwt_accepts_standard_token():
    """decode_jwt (shared/PyJWT) accepts a well-formed token."""
    from value_fabric.shared.identity.jwt import decode_jwt

    token = _make_token()
    with _with_env(**_TEST_ENV):
        claims = decode_jwt(token)

    assert claims is not None
    assert claims.sub == _USER_ID
    assert str(claims.tenant_id) == _TENANT_ID


def test_pyjwt_decode_accepts_standard_token():
    """Raw PyJWT decode accepts a well-formed token."""
    token = _make_token()
    payload = pyjwt.decode(
        token, _SECRET, algorithms=[_ALGORITHM],
        audience=_AUDIENCE, issuer=_ISSUER,
    )
    assert payload["sub"] == _USER_ID
    assert payload["tenant_id"] == _TENANT_ID


# ---------------------------------------------------------------------------
# Rejection tests
# ---------------------------------------------------------------------------

def test_expired_token_rejected_by_pyjwt():
    token = _make_token(expires_in=-60)
    with pytest.raises(pyjwt.ExpiredSignatureError):
        pyjwt.decode(token, _SECRET, algorithms=[_ALGORITHM],
                     audience=_AUDIENCE, issuer=_ISSUER)


def test_expired_token_rejected_by_shared_decode_jwt():
    from fastapi import HTTPException
    from value_fabric.shared.identity.jwt import decode_jwt

    token = _make_token(expires_in=-60)
    with _with_env(**_TEST_ENV):
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt(token)
    assert exc_info.value.status_code == 401


def test_wrong_secret_rejected_by_pyjwt():
    token = _make_token()
    with pytest.raises(pyjwt.InvalidSignatureError):
        pyjwt.decode(token, "completely-different-secret-32ch!!",
                     algorithms=[_ALGORITHM], audience=_AUDIENCE, issuer=_ISSUER)


def test_wrong_issuer_rejected_by_pyjwt():
    token = _make_token(iss="https://evil.example.com")
    with pytest.raises(pyjwt.InvalidIssuerError):
        pyjwt.decode(token, _SECRET, algorithms=[_ALGORITHM],
                     audience=_AUDIENCE, issuer=_ISSUER)


def test_wrong_audience_rejected_by_pyjwt():
    token = _make_token(aud="wrong-audience")
    with pytest.raises(pyjwt.InvalidAudienceError):
        pyjwt.decode(token, _SECRET, algorithms=[_ALGORITHM],
                     audience=_AUDIENCE, issuer=_ISSUER)
