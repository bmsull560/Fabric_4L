"""Tests for dynamic JWKS URL fetching (Keycloak support)."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from unittest.mock import patch

import jwt
import pytest

from value_fabric.shared.identity.jwt import (
    _fetch_jwks_from_url,
    _resolve_external_key,
    decode_jwt,
)


class MockJWKSHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler that returns a mock JWKS."""

    # Generate a single fixed RSA key pair for the lifetime of the server
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    _private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _public_key = _private_key.public_key()

    @classmethod
    def get_jwks(cls):
        from jwt.algorithms import RSAAlgorithm
        jwk = RSAAlgorithm.to_jwk(cls._public_key)
        jwk_obj = json.loads(jwk)
        jwk_obj["kid"] = "test-key-1"
        jwk_obj["alg"] = "RS256"
        jwk_obj["use"] = "sig"
        return {"keys": [jwk_obj]}

    def do_GET(self):
        if self.path == "/jwks":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.get_jwks()).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress logs


@pytest.fixture(scope="module")
def mock_jwks_server():
    server = HTTPServer(("127.0.0.1", 0), MockJWKSHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def test_fetch_jwks_from_url_success(mock_jwks_server):
    url = f"{mock_jwks_server}/jwks"
    jwks = _fetch_jwks_from_url(url)
    assert jwks is not None
    assert "keys" in jwks
    assert len(jwks["keys"]) == 1
    assert jwks["keys"][0]["kid"] == "test-key-1"


def test_fetch_jwks_from_url_caching(mock_jwks_server):
    url = f"{mock_jwks_server}/jwks"
    # First fetch populates cache
    jwks1 = _fetch_jwks_from_url(url)
    # Second fetch should hit cache
    jwks2 = _fetch_jwks_from_url(url)
    assert jwks1 == jwks2


def test_fetch_jwks_from_url_404():
    jwks = _fetch_jwks_from_url("http://127.0.0.1:1/jwks")
    assert jwks is None


def test_resolve_external_key_with_jwks_url(mock_jwks_server):
    url = f"{mock_jwks_server}/jwks"
    with patch.dict("os.environ", {"OIDC_JWKS_URL": url}):
        header = {"kid": "test-key-1", "alg": "RS256"}
        key = _resolve_external_key(header, "https://example.com")
        assert key is not None


def test_resolve_external_key_missing_kid(mock_jwks_server):
    url = f"{mock_jwks_server}/jwks"
    with patch.dict("os.environ", {"OIDC_JWKS_URL": url}):
        header = {"alg": "RS256"}
        key = _resolve_external_key(header, "https://example.com")
        assert key is None


def test_resolve_external_key_revoked_kid(mock_jwks_server):
    url = f"{mock_jwks_server}/jwks"
    with patch.dict("os.environ", {"OIDC_JWKS_URL": url, "JWT_REVOKED_KIDS": "test-key-1"}):
        header = {"kid": "test-key-1", "alg": "RS256"}
        key = _resolve_external_key(header, "https://example.com")
        assert key is None


def test_decode_jwt_with_external_jwks_url(mock_jwks_server):
    from value_fabric.shared.identity import jwt as jwt_module

    # Clear any cached JWKS to ensure fresh fetch
    jwt_module._JWKS_URL_CACHE.clear()
    jwt_module._JWKS_URL_CACHE_EXPIRY.clear()

    url = f"{mock_jwks_server}/jwks"
    # Generate a test token signed with the mock server's private key
    from cryptography.hazmat.primitives import serialization

    private_key = MockJWKSHandler._private_key
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    import time
    now = int(time.time())
    payload = {
        "sub": "test-user",
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "roles": ["analyst"],
        "iss": "https://example.com",
        "aud": "fabric-api",
        "iat": now,
        "exp": now + 3600,
    }
    token = jwt.encode(payload, pem_private, algorithm="RS256", headers={"kid": "test-key-1"})

    with patch.dict(
        "os.environ",
        {
            "OIDC_JWKS_URL": url,
            "OIDC_ISSUER": "https://example.com",
            "OIDC_AUDIENCE": "fabric-api",
            "JWT_ALGORITHM": "RS256",
            "JWT_PUBLIC_KEY_PEM": "dummy",
            "JWT_PRIVATE_KEY_PEM": "dummy",
        },
    ):
        claims = decode_jwt(token)
        assert claims is not None
        assert claims.sub == "test-user"
        assert claims.tenant_id == "550e8400-e29b-41d4-a716-446655440000"
        assert "analyst" in claims.roles
