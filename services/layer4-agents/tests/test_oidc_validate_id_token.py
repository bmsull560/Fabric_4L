from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone

import pytest
from unittest.mock import AsyncMock
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt

from src.shared.identity.oidc import OIDCClient, OIDCProviderConfig, OIDCValidationError


def _b64url_uint(value: int) -> str:
    data = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


@pytest.fixture
def oidc_setup() -> tuple[OIDCClient, rsa.RSAPrivateKey, dict[str, object]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key().public_numbers()
    kid = "test-kid-1"

    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": kid,
                "alg": "RS256",
                "n": _b64url_uint(public_key.n),
                "e": _b64url_uint(public_key.e),
            }
        ]
    }

    config = OIDCProviderConfig(
        issuer="https://issuer.example.com",
        client_id="vf-client",
        jwks_uri="https://issuer.example.com/jwks",
    )
    client = OIDCClient(tenant_id="tenant-1", config=config)
    return client, private_key, jwks


def _make_token(private_key: rsa.RSAPrivateKey, *, issuer: str, audience: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": "user-123",
        "iss": issuer,
        "aud": audience,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "email": "user@example.com",
    }
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test-kid-1", "alg": "RS256"})


@pytest.mark.asyncio
async def test_validate_id_token_accepts_valid_signed_token(oidc_setup):
    client, private_key, jwks = oidc_setup
    client._fetch_jwks = AsyncMock(return_value=jwks)

    token = _make_token(
        private_key,
        issuer="https://issuer.example.com",
        audience="vf-client",
        expires_delta=timedelta(minutes=5),
    )

    claims = await client.validate_id_token(token)
    assert claims.sub == "user-123"


@pytest.mark.asyncio
async def test_validate_id_token_rejects_invalid_signature(oidc_setup):
    client, _private_key, jwks = oidc_setup
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client._fetch_jwks = AsyncMock(return_value=jwks)

    token = _make_token(
        other_key,
        issuer="https://issuer.example.com",
        audience="vf-client",
        expires_delta=timedelta(minutes=5),
    )

    with pytest.raises(OIDCValidationError, match="signature validation failed"):
        await client.validate_id_token(token)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("issuer", "audience"),
    [
        ("https://wrong-issuer.example.com", "vf-client"),
        ("https://issuer.example.com", "wrong-audience"),
    ],
)
async def test_validate_id_token_rejects_wrong_issuer_or_audience(oidc_setup, issuer: str, audience: str):
    client, private_key, jwks = oidc_setup
    client._fetch_jwks = AsyncMock(return_value=jwks)

    token = _make_token(private_key, issuer=issuer, audience=audience, expires_delta=timedelta(minutes=5))

    with pytest.raises(OIDCValidationError, match="mismatch"):
        await client.validate_id_token(token)


@pytest.mark.asyncio
async def test_validate_id_token_rejects_expired_token(oidc_setup):
    client, private_key, jwks = oidc_setup
    client._fetch_jwks = AsyncMock(return_value=jwks)

    token = _make_token(
        private_key,
        issuer="https://issuer.example.com",
        audience="vf-client",
        expires_delta=timedelta(minutes=-5),
    )

    with pytest.raises(OIDCValidationError, match="expired_token"):
        await client.validate_id_token(token)


@pytest.mark.asyncio
async def test_verify_id_token_uses_validate_path(oidc_setup):
    client, private_key, jwks = oidc_setup
    client._fetch_jwks = AsyncMock(return_value=jwks)

    token = _make_token(
        private_key,
        issuer="https://issuer.example.com",
        audience="vf-client",
        expires_delta=timedelta(minutes=5),
    )

    claims = await client.verify_id_token(token)
    assert claims["sub"] == "user-123"
