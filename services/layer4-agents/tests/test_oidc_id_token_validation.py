from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt

from value_fabric.shared.identity.oidc import OIDCClient, OIDCProviderConfig


def _rsa_keypair() -> tuple[rsa.RSAPrivateKey, dict[str, str]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_numbers = private_key.public_key().public_numbers()

    def _b64url_uint(value: int) -> str:
        from jose.utils import base64url_encode

        byte_length = (value.bit_length() + 7) // 8
        return base64url_encode(value.to_bytes(byte_length, "big")).decode("ascii")

    jwk = {
        "kty": "RSA",
        "kid": "kid-1",
        "use": "sig",
        "alg": "RS256",
        "n": _b64url_uint(public_numbers.n),
        "e": _b64url_uint(public_numbers.e),
    }
    return private_key, jwk


def _build_token(private_key: rsa.RSAPrivateKey, issuer: str, audience: str, **claims_overrides):
    now = datetime.now(timezone.utc)
    claims = {
        "sub": "user-123",
        "iss": issuer,
        "aud": audience,
        "iat": int((now - timedelta(seconds=5)).timestamp()),
        "nbf": int((now - timedelta(seconds=5)).timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
    }
    claims.update(claims_overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "kid-1"})


@pytest.fixture
async def oidc_client():
    client = OIDCClient(
        tenant_id="tenant-a",
        config=OIDCProviderConfig(
            issuer="https://issuer.example.com",
            client_id="client-123",
            jwks_uri="https://issuer.example.com/keys",
        ),
    )
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_validate_id_token_invalid_signature(oidc_client: OIDCClient):
    priv1, jwk1 = _rsa_keypair()
    priv2, _ = _rsa_keypair()
    token = _build_token(priv2, oidc_client.config.issuer, oidc_client.config.client_id)

    oidc_client._jwks_cache = {"keys": [jwk1]}
    oidc_client._jwks_cache_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)

    with pytest.raises(ValueError, match="invalid_id_token"):
        await oidc_client.validate_id_token(token)


@pytest.mark.asyncio
async def test_validate_id_token_wrong_issuer(oidc_client: OIDCClient):
    priv, jwk = _rsa_keypair()
    token = _build_token(priv, "https://other-issuer.example.com", oidc_client.config.client_id)
    oidc_client._jwks_cache = {"keys": [jwk]}
    oidc_client._jwks_cache_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)

    with pytest.raises(ValueError, match="invalid_id_token"):
        await oidc_client.validate_id_token(token)


@pytest.mark.asyncio
async def test_validate_id_token_wrong_audience(oidc_client: OIDCClient):
    priv, jwk = _rsa_keypair()
    token = _build_token(priv, oidc_client.config.issuer, "wrong-client")
    oidc_client._jwks_cache = {"keys": [jwk]}
    oidc_client._jwks_cache_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)

    with pytest.raises(ValueError, match="invalid_id_token"):
        await oidc_client.validate_id_token(token)


@pytest.mark.asyncio
async def test_validate_id_token_expired(oidc_client: OIDCClient):
    priv, jwk = _rsa_keypair()
    token = _build_token(
        priv,
        oidc_client.config.issuer,
        oidc_client.config.client_id,
        exp=int((datetime.now(timezone.utc) - timedelta(minutes=10)).timestamp()),
    )
    oidc_client._jwks_cache = {"keys": [jwk]}
    oidc_client._jwks_cache_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)

    with pytest.raises(ValueError, match="expired_token"):
        await oidc_client.validate_id_token(token)


@pytest.mark.asyncio
async def test_validate_id_token_malformed(oidc_client: OIDCClient):
    with pytest.raises(ValueError, match="malformed_token"):
        await oidc_client.validate_id_token("not-a-jwt")


@pytest.mark.asyncio
async def test_validate_id_token_jwks_refresh_on_rotation(oidc_client: OIDCClient):
    priv_old, jwk_old = _rsa_keypair()
    priv_new, jwk_new = _rsa_keypair()
    jwk_old["kid"] = "kid-old"
    jwk_new["kid"] = "kid-new"

    token = jwt.encode(
        {
            "sub": "user-123",
            "iss": oidc_client.config.issuer,
            "aud": oidc_client.config.client_id,
            "iat": int((datetime.now(timezone.utc) - timedelta(seconds=5)).timestamp()),
            "nbf": int((datetime.now(timezone.utc) - timedelta(seconds=5)).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
        },
        priv_new,
        algorithm="RS256",
        headers={"kid": "kid-new"},
    )

    oidc_client._jwks_cache = {"keys": [jwk_old]}
    oidc_client._jwks_cache_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)

    calls = {"count": 0}

    async def _fake_fetch(*, force_refresh: bool = False):
        calls["count"] += 1
        return {"keys": [jwk_new]} if force_refresh else {"keys": [jwk_old]}

    oidc_client._fetch_jwks = _fake_fetch  # type: ignore[method-assign]

    claims = await oidc_client.validate_id_token(token)
    assert claims.sub == "user-123"
    assert calls["count"] >= 2
