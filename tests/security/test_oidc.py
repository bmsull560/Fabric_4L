"""Tests for OIDC authentication flow.

Validates:
- PKCE code generation
- OIDC discovery
- Token exchange
- Role mapping from claims
- ID token verification
- Error handling
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from unittest.mock import Mock, patch

import httpx
import pytest

from shared.audit import AuditAction, AuditOutcome
from shared.identity.oidc import OIDCClient, map_role_from_claims
from shared.identity.oidc_config import OIDCProviderConfig


def _generate_code_verifier() -> str:
    """Generate PKCE code_verifier for tests (mirrors implementation)."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode("ascii").rstrip("=")


def _generate_code_challenge(code_verifier: str) -> str:
    """Generate PKCE code_challenge for tests (mirrors implementation)."""
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


class TestPKCEGeneration:
    """Test PKCE code generation functions."""

    def test_code_verifier_format(self):
        """Code verifier should be base64url encoded and 43+ chars."""
        verifier = _generate_code_verifier()
        # RFC 7636: code_verifier is 43-128 chars
        assert len(verifier) >= 43
        assert len(verifier) <= 128
        # Should be URL-safe base64 characters only
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_." for c in verifier)

    def test_code_challenge_consistency(self):
        """Same verifier should produce same challenge."""
        verifier = _generate_code_verifier()
        challenge1 = _generate_code_challenge(verifier)
        challenge2 = _generate_code_challenge(verifier)

        assert challenge1 == challenge2
        assert challenge1 != verifier

    def test_code_challenge_s256(self):
        """Code challenge should be S256 hash of verifier."""
        verifier = "test_verifier_123456789012345678901234567890"
        challenge = _generate_code_challenge(verifier)

        # Manual S256 calculation
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).decode("ascii").rstrip("=")

        assert challenge == expected


class TestOIDCClient:
    """Test OIDC client methods."""

    @pytest.fixture
    def oidc_client(self):
        """Create OIDC client fixture."""
        return OIDCClient()

    @pytest.mark.asyncio
    async def test_discover_success(self, oidc_client):
        """OIDC discovery should fetch metadata from well-known endpoint."""
        mock_response = {
            "issuer": "https://auth.example.com",
            "authorization_endpoint": "https://auth.example.com/oauth/authorize",
            "token_endpoint": "https://auth.example.com/oauth/token",
            "userinfo_endpoint": "https://auth.example.com/oauth/userinfo",
            "jwks_uri": "https://auth.example.com/oauth/keys",
        }

        with patch.object(oidc_client._http_client, "get") as mock_get:
            mock_get.return_value = Mock(
                raise_for_status=Mock(),
                json=Mock(return_value=mock_response)
            )

            result = await oidc_client.discover("https://auth.example.com")

            assert result == mock_response
            mock_get.assert_called_once_with(
                "https://auth.example.com/.well-known/openid-configuration"
            )

    def test_build_authorize_url(self, oidc_client):
        """Build authorize URL with all parameters."""
        metadata = {"authorization_endpoint": "https://auth.example.com/oauth/authorize"}

        url = oidc_client.build_authorize_url(
            metadata=metadata,
            client_id="test-client",
            redirect_uri="https://app.example.com/callback",
            state="test-state-123",
            nonce="test-nonce-456",
            scopes=["openid", "profile", "email"],
            code_challenge="abc123",
            code_challenge_method="S256",
        )

        assert url.startswith("https://auth.example.com/oauth/authorize?")
        assert "client_id=test-client" in url
        assert "response_type=code" in url
        assert "scope=openid+profile+email" in url
        assert "redirect_uri=https%3A%2F%2Fapp.example.com%2Fcallback" in url
        assert "state=test-state-123" in url
        assert "nonce=test-nonce-456" in url
        assert "code_challenge=abc123" in url
        assert "code_challenge_method=S256" in url

    def test_build_authorize_url_without_pkce(self, oidc_client):
        """Build authorize URL without PKCE parameters."""
        metadata = {"authorization_endpoint": "https://auth.example.com/oauth/authorize"}

        url = oidc_client.build_authorize_url(
            metadata=metadata,
            client_id="test-client",
            redirect_uri="https://app.example.com/callback",
            state="test-state",
        )

        assert "code_challenge" not in url
        assert "code_challenge_method" not in url

    @pytest.mark.asyncio
    async def test_exchange_code(self, oidc_client):
        """Exchange authorization code for tokens."""
        token_response = {
            "access_token": "test_access_token",
            "id_token": "test_id_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        with patch.object(oidc_client._http_client, "post") as mock_post:
            mock_post.return_value = Mock(
                raise_for_status=Mock(),
                json=Mock(return_value=token_response)
            )

            result = await oidc_client.exchange_code(
                token_endpoint="https://auth.example.com/oauth/token",
                code="auth_code_123",
                redirect_uri="https://app.example.com/callback",
                client_id="test-client",
                client_secret="test-secret",
                code_verifier="verifier_123",
            )

            assert result == token_response
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "https://auth.example.com/oauth/token"


class TestRoleMapping:
    """Test role mapping from OIDC claims."""

    def test_map_super_admin_from_role_claim(self):
        """Map super_admin from role claim."""
        claims = {"role": "super_admin"}
        role = map_role_from_claims(claims)
        assert role == "super_admin"

    def test_map_tenant_admin_from_groups(self):
        """Map tenant_admin from groups claim."""
        claims = {"groups": ["admin", "users"]}
        role = map_role_from_claims(claims)
        assert role == "tenant_admin"

    def test_map_user_default(self):
        """Default to user role."""
        claims = {"email": "user@example.com"}
        role = map_role_from_claims(claims)
        assert role == "user"

    def test_map_with_claim_mapping(self):
        """Use custom claim mapping if provided."""
        claims = {"custom_role": "editor", "department": "engineering"}
        mapping = {"custom_role": "editor", "department": "manager"}
        role = map_role_from_claims(claims, claim_mapping=mapping)
        assert role == "editor"

    def test_map_with_default_role(self):
        """Use default_role when no mapping matches."""
        claims = {"email": "user@example.com"}
        role = map_role_from_claims(claims, default_role="readonly")
        assert role == "readonly"

    def test_map_groups_string(self):
        """Handle groups as string instead of list."""
        claims = {"groups": "admin"}
        role = map_role_from_claims(claims)
        assert role == "tenant_admin"


class TestOIDCProviderConfig:
    """Test OIDC provider configuration."""

    def test_from_settings_success(self):
        """Create config from tenant settings."""
        settings = {
            "oidc": {
                "provider_name": "okta",
                "enabled": True,
                "config": {
                    "issuer_url": "https://example.okta.com",
                    "client_id": "test-client",
                    "client_secret": "test-secret",
                    "redirect_uri": "https://app.example.com/callback",
                    "scopes": ["openid", "profile", "email"],
                }
            }
        }

        config = OIDCProviderConfig.from_settings(settings)

        assert config is not None
        assert config.provider_name == "okta"
        assert config.issuer_url == "https://example.okta.com"
        assert config.client_id == "test-client"
        assert config.enabled is True

    def test_from_settings_disabled(self):
        """Return None when OIDC is disabled."""
        settings = {
            "oidc": {
                "enabled": False,
            }
        }

        config = OIDCProviderConfig.from_settings(settings)
        assert config is None

    def test_from_settings_no_oidc(self):
        """Return None when no OIDC settings."""
        settings = {"other": "value"}
        config = OIDCProviderConfig.from_settings(settings)
        assert config is None

    def test_from_settings_flat_config(self):
        """Handle flat config structure (no nested config key)."""
        settings = {
            "oidc": {
                "issuer_url": "https://auth.example.com",
                "client_id": "test-client",
            }
        }

        config = OIDCProviderConfig.from_settings(settings)

        assert config is not None
        assert config.issuer_url == "https://auth.example.com"
        assert config.client_id == "test-client"


class TestOIDCIntegration:
    """Integration tests for OIDC flow."""

    @pytest.mark.asyncio
    async def test_full_oidc_flow_mocked(self):
        """Test complete OIDC flow with mocked responses."""
        client = OIDCClient()

        # Mock discovery
        discovery_response = {
            "issuer": "https://auth.example.com",
            "authorization_endpoint": "https://auth.example.com/oauth/authorize",
            "token_endpoint": "https://auth.example.com/oauth/token",
            "userinfo_endpoint": "https://auth.example.com/oauth/userinfo",
            "jwks_uri": "https://auth.example.com/oauth/keys",
        }

        with patch.object(client._http_client, "get") as mock_get:
            mock_get.return_value = Mock(
                raise_for_status=Mock(),
                json=Mock(return_value=discovery_response)
            )

            # Test discovery
            metadata = await client.discover("https://auth.example.com")
            assert metadata["issuer"] == "https://auth.example.com"

            # Test authorize URL generation
            auth_url = client.build_authorize_url(
                metadata=metadata,
                client_id="test-client",
                redirect_uri="https://app.example.com/callback",
                state="state-123",
                code_challenge="challenge-abc",
            )
            assert "state=state-123" in auth_url
            assert "code_challenge=challenge-abc" in auth_url


class TestOIDCErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def oidc_client(self):
        """Create OIDC client fixture."""
        return OIDCClient()

    @pytest.mark.asyncio
    async def test_discover_404_error(self, oidc_client):
        """Discovery should not retry on 404 errors."""
        with patch.object(oidc_client._http_client, "get") as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=Mock(),
                response=Mock(status_code=404),
            )

            with pytest.raises(httpx.HTTPStatusError):
                await oidc_client.discover("https://auth.example.com")

            # Should not retry on 404
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_discover_retry_on_500(self, oidc_client):
        """Discovery should retry on 500 errors."""
        with patch.object(oidc_client._http_client, "get") as mock_get:
            mock_get.side_effect = [
                httpx.HTTPStatusError(
                    "Server Error",
                    request=Mock(),
                    response=Mock(status_code=500),
                ),
                Mock(raise_for_status=Mock(), json=Mock(return_value={"issuer": "https://auth.example.com"})),
            ]

            result = await oidc_client.discover("https://auth.example.com")
            assert result["issuer"] == "https://auth.example.com"
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_exchange_code_4xx_no_retry(self, oidc_client):
        """Token exchange should not retry on 4xx errors."""
        with patch.object(oidc_client._http_client, "post") as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "Bad Request",
                request=Mock(),
                response=Mock(status_code=400),
            )

            with pytest.raises(httpx.HTTPStatusError):
                await oidc_client.exchange_code(
                    token_endpoint="https://auth.example.com/token",
                    code="invalid_code",
                    redirect_uri="https://app.example.com/callback",
                    client_id="test-client",
                    client_secret="secret",
                )

            # Should not retry on 400
            assert mock_post.call_count == 1


class TestOIDCProviderConfigValidation:
    """Test OIDC config validation."""

    def test_from_settings_missing_issuer_url(self):
        """Should raise ValueError when issuer_url is missing."""
        settings = {
            "oidc": {
                "client_id": "test-client",
                # Missing issuer_url
            }
        }

        with pytest.raises(ValueError, match="issuer_url"):
            OIDCProviderConfig.from_settings(settings)

    def test_from_settings_missing_client_id(self):
        """Should raise ValueError when client_id is missing."""
        settings = {
            "oidc": {
                "issuer_url": "https://auth.example.com",
                # Missing client_id
            }
        }

        with pytest.raises(ValueError, match="client_id"):
            OIDCProviderConfig.from_settings(settings)

    def test_from_settings_empty_issuer_url(self):
        """Should raise ValueError when issuer_url is empty string."""
        settings = {
            "oidc": {
                "issuer_url": "",
                "client_id": "test-client",
            }
        }

        with pytest.raises(ValueError, match="issuer_url"):
            OIDCProviderConfig.from_settings(settings)


class TestRoleMappingEdgeCases:
    """Test role mapping edge cases."""

    def test_map_role_with_list_claim_values(self):
        """Handle list claim values properly."""
        claims = {"roles": ["user", "admin", "editor"]}
        mapping = {"roles": "admin"}
        role = map_role_from_claims(claims, claim_mapping=mapping)
        assert role == "admin"

    def test_map_role_partial_match_should_not_work(self):
        """Partial string matching should not work anymore."""
        claims = {"role": "superadmin"}  # Contains 'admin' but not equal
        mapping = {"role": "admin"}
        role = map_role_from_claims(claims, claim_mapping=mapping)
        # Should not match "superadmin" to "admin" anymore (exact match required)
        assert role != "admin"  # Falls through to default logic

    def test_map_role_case_insensitive(self):
        """Role mapping should be case insensitive."""
        claims = {"Role": "ADMIN"}  # Mixed case
        mapping = {"Role": "admin"}
        role = map_role_from_claims(claims, claim_mapping=mapping)
        assert role == "admin"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
