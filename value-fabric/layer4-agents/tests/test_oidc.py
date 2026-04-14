"""Unit tests for OIDC client, claim mapping, and callback flow."""

from __future__ import annotations

import os

# Ensure layer4-agents src is importable
import sys
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import jwt
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.identity.oidc import _JWKS_CACHE, OIDCClient, map_role_from_claims


class TestClaimMapping:
    """Tests for the OIDC claim → role mapping engine."""

    def test_exact_string_match(self) -> None:
        claims = {"role": "admin"}
        result = map_role_from_claims(claims, {"role=admin": "tenant_admin"}, "read_only")
        assert result == "tenant_admin"

    def test_nested_claim_path(self) -> None:
        claims = {"groups": {"value": "analysts"}}
        result = map_role_from_claims(
            claims, {"groups.value=analysts": "analyst"}, "read_only"
        )
        assert result == "analyst"

    def test_array_membership_match(self) -> None:
        claims = {"groups": ["users", "admins"]}
        result = map_role_from_claims(
            claims, {"groups=admins": "tenant_admin"}, "read_only"
        )
        assert result == "tenant_admin"

    def test_regex_match(self) -> None:
        claims = {"email": "admin@example.com"}
        result = map_role_from_claims(
            claims, {"email=/@example\\.com$/": "analyst"}, "read_only"
        )
        assert result == "analyst"

    def test_regex_match_with_role(self) -> None:
        claims = {"department": "engineering-leads"}
        result = map_role_from_claims(
            claims, {"department=/^engineering-.*/": "content_admin"}, "read_only"
        )
        assert result == "content_admin"

    def test_highest_privilege_wins(self) -> None:
        claims = {"role": "super_admin"}
        mapping = {"role": "super_admin"}
        result = map_role_from_claims(claims, mapping, "read_only")
        assert result == "super_admin"

    def test_fallback_to_default(self) -> None:
        claims = {"role": "unknown"}
        result = map_role_from_claims(claims, {"role=admin": "tenant_admin"}, "analyst")
        assert result == "analyst"


class TestOIDCClient:
    """Tests for OIDCClient discovery and token verification."""

    @pytest.fixture(autouse=True)
    def _clear_jwks_cache(self) -> None:
        _JWKS_CACHE.clear()

    @pytest.mark.asyncio
    async def test_discover(self) -> None:
        client = OIDCClient(http_client=MagicMock())
        client._http.get = AsyncMock(return_value=MagicMock(json=lambda: {"issuer": "https://idp.example.com"}))
        meta = await client.discover("https://idp.example.com")
        assert meta["issuer"] == "https://idp.example.com"

    @pytest.mark.asyncio
    async def test_build_authorize_url(self) -> None:
        client = OIDCClient()
        url = client.build_authorize_url(
            metadata={"authorization_endpoint": "https://idp.example.com/auth"},
            client_id="client-123",
            redirect_uri="https://app.example.com/callback",
            state="abc",
            nonce="def",
            scopes=["openid", "email"],
        )
        assert "https://idp.example.com/auth?" in url
        assert "client_id=client-123" in url
        assert "state=abc" in url
        assert "nonce=def" in url
        assert "scope=openid+email" in url

    @pytest.mark.asyncio
    async def test_verify_id_token_with_mocked_jwks(self) -> None:
        # Generate a temporary RSA key pair
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        public_key = private_key.public_key()

        # Build JWKS
        pub_numbers = public_key.public_numbers()
        e_bytes = pub_numbers.e.to_bytes((pub_numbers.e.bit_length() + 7) // 8, "big")
        n_bytes = pub_numbers.n.to_bytes((pub_numbers.n.bit_length() + 7) // 8, "big")
        import base64

        jwk = {
            "kty": "RSA",
            "kid": "key-1",
            "use": "sig",
            "n": base64.urlsafe_b64encode(n_bytes).rstrip(b"=").decode(),
            "e": base64.urlsafe_b64encode(e_bytes).rstrip(b"=").decode(),
            "alg": "RS256",
        }

        # Encode a test id_token
        now = int(time.time())
        token = jwt.encode(
            {
                "iss": "https://idp.example.com",
                "aud": "client-123",
                "sub": "user-1",
                "email": "user@example.com",
                "iat": now,
                "exp": now + 300,
            },
            key=private_key,
            algorithm="RS256",
            headers={"kid": "key-1"},
        )

        http_client = MagicMock()
        http_client.get = AsyncMock(
            side_effect=[
                MagicMock(json=lambda: {"jwks_uri": "https://idp.example.com/jwks"}),
                MagicMock(json=lambda: {"keys": [jwk]}),
            ]
        )

        client = OIDCClient(http_client=http_client)
        claims = await client.verify_id_token(
            id_token=token,
            issuer_url="https://idp.example.com",
            client_id="client-123",
        )
        assert claims["sub"] == "user-1"
        assert claims["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_exchange_code(self) -> None:
        client = OIDCClient(http_client=MagicMock())
        client._http.post = AsyncMock(
            return_value=MagicMock(json=lambda: {"access_token": "at", "id_token": "it"})
        )
        result = await client.exchange_code(
            token_endpoint="https://idp.example.com/token",
            code="authcode",
            redirect_uri="https://app.example.com/callback",
            client_id="client-123",
            client_secret="secret",
        )
        assert result["access_token"] == "at"
        assert result["id_token"] == "it"


class TestOIDCRoutes:
    """Tests for OIDC FastAPI routes (with mocked DB and IdP)."""

    @pytest.fixture
    def dummy_tenant(self) -> MagicMock:
        tenant = MagicMock()
        tenant.id = uuid4()
        tenant.slug = "acme"
        tenant.settings = {
            "oidc": {
                "provider_name": "test-idp",
                "issuer_url": "https://idp.example.com",
                "client_id": "client-123",
                "client_secret_ref": "OIDC_TEST_SECRET",
                "scopes": ["openid", "email"],
                "claim_mapping": {"role=analyst": "analyst"},
                "default_role": "read_only",
                "auto_provision_users": True,
                "enabled": True,
            }
        }
        return tenant

    @pytest.mark.asyncio
    async def test_oidc_login_returns_auth_url(self, dummy_tenant: MagicMock) -> None:

        from src.tenants.api.routes.oidc import oidc_login

        db = AsyncMock()
        db.execute = AsyncMock()
        # First call: tenant lookup
        # Second call: insert session
        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none = MagicMock(return_value=dummy_tenant)
        session_result = MagicMock()
        session_result.mappings.return_value.one_or_none = MagicMock(return_value=None)

        db.execute.side_effect = [tenant_result, session_result]

        with patch("src.tenants.api.routes.oidc.OIDCClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.discover = AsyncMock(
                return_value={"authorization_endpoint": "https://idp.example.com/auth"}
            )
            mock_client.build_authorize_url = MagicMock(
                return_value="https://idp.example.com/auth?client_id=client-123"
            )
            mock_client_cls.return_value = mock_client

            result = await oidc_login("acme", db=db)
            assert "authorization_url" in result
            assert result["authorization_url"].startswith("https://idp.example.com/auth")

    @pytest.mark.asyncio
    async def test_oidc_callback_auto_provisions_user(self, dummy_tenant: MagicMock) -> None:
        from fastapi import Request

        from src.tenants.api.routes.oidc import oidc_callback

        tenant_id = dummy_tenant.id
        state = "state-123"

        # Mock request
        request = MagicMock(spec=Request)

        # Mock DB
        db = AsyncMock()

        # Session row
        session_row = {
            "tenant_id": tenant_id,
            "nonce": "nonce-123",
            "redirect_uri": "https://localhost/callback",
            "expires_at": datetime.now(UTC) + timedelta(minutes=10),
        }

        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none = MagicMock(return_value=dummy_tenant)

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=None)

        # Build side effects for db.execute calls
        # 1: select oidc_sessions
        # 2: delete oidc_sessions (state)
        # 3: select tenant
        # 4: select user
        # 5: commit
        # Note: some are text() calls; we just return the right mocks
        r1 = MagicMock()
        r1.mappings.return_value.one_or_none = MagicMock(return_value=session_row)
        r2 = MagicMock()
        r3 = tenant_result
        r4 = user_result

        db.execute.side_effect = [r1, r2, r3, r4]

        # Mock token verification
        with patch("src.tenants.api.routes.oidc.OIDCClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.discover = AsyncMock(
                return_value={"token_endpoint": "https://idp.example.com/token"}
            )
            mock_client.exchange_code = AsyncMock(
                return_value={"id_token": "dummy_id_token"}
            )
            mock_client.verify_id_token = AsyncMock(
                return_value={
                    "sub": "oidc-user-1",
                    "email": "newuser@example.com",
                    "role": "analyst",
                    "nonce": "nonce-123",
                }
            )
            mock_client_cls.return_value = mock_client

            result = await oidc_callback(
                request=request,
                state=state,
                code="authcode",
                db=db,
            )
            assert result["token_type"] == "Bearer"
            assert "access_token" in result
            assert result["email"] == "newuser@example.com"

    @pytest.mark.asyncio
    async def test_oidc_callback_rejects_disabled_oidc(self, dummy_tenant: MagicMock) -> None:
        from fastapi import HTTPException

        from src.tenants.api.routes.oidc import oidc_login

        dummy_tenant.settings["oidc"]["enabled"] = False
        db = AsyncMock()
        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none = MagicMock(return_value=dummy_tenant)
        db.execute.return_value = tenant_result

        with pytest.raises(HTTPException) as exc_info:
            await oidc_login("acme", db=db)
        assert exc_info.value.status_code == 400
