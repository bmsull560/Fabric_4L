"""JWT validation regression tests for shared identity decoding behavior."""

from __future__ import annotations

import time
from unittest.mock import patch

import jwt

from value_fabric.shared.identity.jwt import decode_jwt


TEST_SECRET = "jwt-validation-test-secret"
TEST_AUDIENCE = "value-fabric-services"
TEST_ISSUER = "value-fabric-internal"
TEST_TENANT_ID = "11111111-1111-1111-1111-111111111111"



def _sign(payload: dict, *, secret: str = TEST_SECRET, kid: str | None = None) -> str:
    headers = {"kid": kid} if kid else None
    return jwt.encode(payload, secret, algorithm="HS256", headers=headers)


@patch.dict(
    "os.environ",
    {
        "JWT_SECRET": TEST_SECRET,
        "JWT_ALGORITHM": "HS256",
        "JWT_ISSUER": TEST_ISSUER,
        "JWT_AUDIENCE": TEST_AUDIENCE,
    },
    clear=False,
)
def test_decode_rejects_wrong_issuer() -> None:
    token = _sign(
        {
            "tenant_id": TEST_TENANT_ID,
            "iss": "unexpected-issuer",
            "aud": TEST_AUDIENCE,
            "exp": int(time.time()) + 600,
        }
    )

    assert decode_jwt(token) is None


@patch.dict(
    "os.environ",
    {
        "JWT_SECRET": TEST_SECRET,
        "JWT_ALGORITHM": "HS256",
        "JWT_ISSUER": TEST_ISSUER,
        "JWT_AUDIENCE": TEST_AUDIENCE,
        "JWT_REVOKED_KIDS": "revoked-kid",
    },
    clear=False,
)
def test_decode_rejects_revoked_kid() -> None:
    token = _sign(
        {
            "tenant_id": TEST_TENANT_ID,
            "iss": TEST_ISSUER,
            "aud": TEST_AUDIENCE,
            "exp": int(time.time()) + 600,
        },
        kid="revoked-kid",
    )

    assert decode_jwt(token) is None


@patch.dict(
    "os.environ",
    {
        "JWT_SECRET": TEST_SECRET,
        "JWT_ALGORITHM": "HS256",
        "JWT_ISSUER": TEST_ISSUER,
        "JWT_AUDIENCE": TEST_AUDIENCE,
    },
    clear=False,
)
def test_decode_accepts_valid_internal_token() -> None:
    token = _sign(
        {
            "tenant_id": TEST_TENANT_ID,
            "sub": "user-1",
            "roles": ["analyst"],
            "iss": TEST_ISSUER,
            "aud": TEST_AUDIENCE,
            "exp": int(time.time()) + 600,
            "iat": int(time.time()),
        }
    )

    claims = decode_jwt(token)

    assert claims is not None
    assert claims.tenant_id == TEST_TENANT_ID
    assert claims.sub == "user-1"
    assert claims.roles == ["analyst"]
