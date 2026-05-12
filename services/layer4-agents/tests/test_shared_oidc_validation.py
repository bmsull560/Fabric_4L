from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.shared.identity.oidc import (
    OIDCClient,
    OIDCProviderConfig,
    OIDCValidationError,
    validate_tenant_oidc_provider_mapping,
)


def _rsa_material() -> tuple[str, dict[str, str]]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    jwk["kid"] = "kid-1"
    return private_pem.decode("utf-8"), jwk


@pytest.fixture
def oidc_client() -> OIDCClient:
    config = OIDCProviderConfig(
        issuer="https://issuer.tenant-a.example.com",
        client_id="tenant-a-client",
        jwks_uri="https://issuer.tenant-a.example.com/jwks",
    )
    return OIDCClient(tenant_id="tenant-a", config=config)


@pytest.mark.asyncio
async def test_validate_id_token_forged_signature_rejected(oidc_client: OIDCClient) -> None:
    _, jwk = _rsa_material()
    oidc_client._fetch_jwks = lambda: {"keys": [jwk]}  # type: ignore[method-assign]
    payload = {
        "sub": "user-1",
        "iss": oidc_client.config.issuer,
        "aud": oidc_client.config.client_id,
        "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
        "nonce": "nonce-ok",
    }
    token = jwt.encode(payload, "wrong-secret", algorithm="HS256", headers={"kid": "kid-1"})
    with pytest.raises(OIDCValidationError, match="algorithm"):
        await oidc_client.validate_id_token(token, expected_nonce="nonce-ok")


@pytest.mark.asyncio
async def test_validate_id_token_wrong_audience_rejected(oidc_client: OIDCClient) -> None:
    private_pem, jwk = _rsa_material()
    oidc_client._fetch_jwks = lambda: {"keys": [jwk]}  # type: ignore[method-assign]
    payload = {
        "sub": "user-1",
        "iss": oidc_client.config.issuer,
        "aud": "wrong-audience",
        "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
        "nonce": "nonce-ok",
    }
    token = jwt.encode(payload, private_pem, algorithm="RS256", headers={"kid": "kid-1"})
    with pytest.raises(OIDCValidationError, match="audience"):
        await oidc_client.validate_id_token(token, expected_nonce="nonce-ok")


@pytest.mark.asyncio
async def test_validate_id_token_wrong_issuer_rejected(oidc_client: OIDCClient) -> None:
    private_pem, jwk = _rsa_material()
    oidc_client._fetch_jwks = lambda: {"keys": [jwk]}  # type: ignore[method-assign]
    payload = {
        "sub": "user-1",
        "iss": "https://issuer.tenant-b.example.com",
        "aud": oidc_client.config.client_id,
        "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
        "nonce": "nonce-ok",
    }
    token = jwt.encode(payload, private_pem, algorithm="RS256", headers={"kid": "kid-1"})
    with pytest.raises(OIDCValidationError, match="issuer"):
        await oidc_client.validate_id_token(token, expected_nonce="nonce-ok")


@pytest.mark.asyncio
async def test_validate_id_token_stale_jwks_rejected(oidc_client: OIDCClient) -> None:
    private_pem, jwk = _rsa_material()
    token = jwt.encode(
        {
            "sub": "user-1",
            "iss": oidc_client.config.issuer,
            "aud": oidc_client.config.client_id,
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
            "iat": int(datetime.now(UTC).timestamp()),
            "nonce": "nonce-ok",
        },
        private_pem,
        algorithm="RS256",
        headers={"kid": "unknown-kid"},
    )
    oidc_client._fetch_jwks = lambda: {"keys": [jwk]}  # type: ignore[method-assign]
    with pytest.raises(OIDCValidationError, match="stale"):
        await oidc_client.validate_id_token(token, expected_nonce="nonce-ok")


@pytest.mark.asyncio
async def test_validate_id_token_replayed_nonce_or_state_rejected(oidc_client: OIDCClient) -> None:
    private_pem, jwk = _rsa_material()
    oidc_client._fetch_jwks = lambda: {"keys": [jwk]}  # type: ignore[method-assign]
    token = jwt.encode(
        {
            "sub": "user-1",
            "iss": oidc_client.config.issuer,
            "aud": oidc_client.config.client_id,
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
            "iat": int(datetime.now(UTC).timestamp()),
            "nonce": "nonce-original",
        },
        private_pem,
        algorithm="RS256",
        headers={"kid": "kid-1"},
    )
    with pytest.raises(OIDCValidationError, match="nonce"):
        await oidc_client.validate_id_token(token, expected_nonce="nonce-different", callback_state="s1", stored_state="s1")

    with pytest.raises(OIDCValidationError, match="state mismatch"):
        await oidc_client.validate_id_token(token, expected_nonce="nonce-original", callback_state="s2", stored_state="s1")


def test_validate_tenant_oidc_provider_mapping_rejects_cross_tenant() -> None:
    config = OIDCProviderConfig(
        issuer="https://issuer.tenant-a.example.com",
        client_id="tenant-a-client",
        jwks_uri="https://issuer.tenant-a.example.com/jwks",
    )
    with pytest.raises(OIDCValidationError, match="issuer mapping mismatch"):
        validate_tenant_oidc_provider_mapping(
            tenant_id="tenant-b",
            expected_issuer="https://issuer.tenant-b.example.com",
            expected_client_id="tenant-b-client",
            provider_config=config,
        )
