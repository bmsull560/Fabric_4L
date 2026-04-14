"""Tests for JWT encode/decode helpers (shared/identity/jwt.py)."""

import os
import time
from unittest.mock import patch
from uuid import UUID, uuid4

import jwt as pyjwt
import pytest
from fastapi import HTTPException

from ..jwt import TokenClaims, decode_jwt, encode_jwt


# Use a fixed secret across all tests to avoid env-var interference
_TEST_SECRET = "test-jwt-secret-for-unit-tests"
_TEST_TENANT = uuid4()


@pytest.fixture(autouse=True)
def _jwt_env():
    """Set predictable JWT env vars for every test."""
    with patch.dict(
        os.environ,
        {
            "JWT_SECRET": _TEST_SECRET,
            "JWT_ALGORITHM": "HS256",
        },
    ):
        yield


# ---------------------------------------------------------------------------
# TokenClaims
# ---------------------------------------------------------------------------


class TestTokenClaims:
    """Tests for the TokenClaims dataclass."""

    def test_has_role_present(self):
        tc = TokenClaims(tenant_id=_TEST_TENANT, roles=["analyst", "read_only"])
        assert tc.has_role("analyst") is True

    def test_has_role_absent(self):
        tc = TokenClaims(tenant_id=_TEST_TENANT, roles=["analyst"])
        assert tc.has_role("super_admin") is False

    def test_require_role_passes(self):
        tc = TokenClaims(tenant_id=_TEST_TENANT, roles=["super_admin"])
        tc.require_role("super_admin")  # should not raise

    def test_require_role_raises_403(self):
        tc = TokenClaims(tenant_id=_TEST_TENANT, roles=["analyst"])
        with pytest.raises(HTTPException) as exc_info:
            tc.require_role("super_admin")
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# encode_jwt
# ---------------------------------------------------------------------------


class TestEncodeJwt:
    """Tests for encode_jwt()."""

    def test_basic_encode(self):
        """Produces a decodable JWT string."""
        token = encode_jwt(_TEST_TENANT)
        payload = pyjwt.decode(token, _TEST_SECRET, algorithms=["HS256"])
        assert payload["tenant_id"] == str(_TEST_TENANT)

    def test_includes_exp_claim(self):
        token = encode_jwt(_TEST_TENANT, expires_in_seconds=600)
        payload = pyjwt.decode(token, _TEST_SECRET, algorithms=["HS256"])
        assert "exp" in payload
        assert "iat" in payload
        assert payload["exp"] - payload["iat"] == 600

    def test_includes_user_id(self):
        token = encode_jwt(_TEST_TENANT, user_id="user-42")
        payload = pyjwt.decode(token, _TEST_SECRET, algorithms=["HS256"])
        assert payload["sub"] == "user-42"

    def test_includes_roles(self):
        token = encode_jwt(_TEST_TENANT, roles=["analyst", "content_admin"])
        payload = pyjwt.decode(token, _TEST_SECRET, algorithms=["HS256"])
        assert payload["roles"] == ["analyst", "content_admin"]

    def test_includes_api_key_id(self):
        token = encode_jwt(_TEST_TENANT, api_key_id="key-99")
        payload = pyjwt.decode(token, _TEST_SECRET, algorithms=["HS256"])
        assert payload["api_key_id"] == "key-99"

    def test_extra_claims_merged(self):
        token = encode_jwt(_TEST_TENANT, extra_claims={"custom": "value"})
        payload = pyjwt.decode(token, _TEST_SECRET, algorithms=["HS256"])
        assert payload["custom"] == "value"


# ---------------------------------------------------------------------------
# decode_jwt
# ---------------------------------------------------------------------------


class TestDecodeJwt:
    """Tests for decode_jwt()."""

    def test_valid_token(self):
        """Round-trip: encode → decode produces matching claims."""
        token = encode_jwt(
            _TEST_TENANT,
            user_id="user-1",
            roles=["analyst"],
            api_key_id="key-1",
        )
        claims = decode_jwt(token)
        assert claims is not None
        assert claims.tenant_id == _TEST_TENANT
        assert claims.user_id == "user-1"
        assert claims.roles == ["analyst"]
        assert claims.api_key_id == "key-1"

    def test_expired_token_raises_401(self):
        """An expired token raises HTTPException(401)."""
        token = encode_jwt(_TEST_TENANT, expires_in_seconds=-1)
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt(token)
        assert exc_info.value.status_code == 401

    def test_invalid_signature_returns_none(self):
        """A token signed with the wrong secret returns None."""
        bad_token = pyjwt.encode(
            {"tenant_id": str(_TEST_TENANT), "exp": int(time.time()) + 3600},
            "wrong-secret",
            algorithm="HS256",
        )
        assert decode_jwt(bad_token) is None

    def test_missing_tenant_claim_returns_none(self):
        """A token without the tenant_id claim returns None."""
        token = pyjwt.encode(
            {"exp": int(time.time()) + 3600},
            _TEST_SECRET,
            algorithm="HS256",
        )
        assert decode_jwt(token) is None

    def test_invalid_tenant_uuid_returns_none(self):
        """A token with a non-UUID tenant_id returns None."""
        token = pyjwt.encode(
            {"tenant_id": "not-a-uuid", "exp": int(time.time()) + 3600},
            _TEST_SECRET,
            algorithm="HS256",
        )
        assert decode_jwt(token) is None

    def test_roles_as_string_converted_to_list(self):
        """A single role string is wrapped into a list."""
        token = pyjwt.encode(
            {
                "tenant_id": str(_TEST_TENANT),
                "roles": "analyst",
                "exp": int(time.time()) + 3600,
            },
            _TEST_SECRET,
            algorithm="HS256",
        )
        claims = decode_jwt(token)
        assert claims is not None
        assert claims.roles == ["analyst"]

    def test_malformed_token_returns_none(self):
        """Garbage input returns None."""
        assert decode_jwt("not.a.jwt") is None
        assert decode_jwt("") is None
