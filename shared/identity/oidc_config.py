"""OIDC provider configuration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class OIDCProviderConfig(BaseModel):
    """Configuration for an OIDC provider."""

    provider_name: str = Field(default="oidc", description="Provider identifier")
    issuer_url: str = Field(..., description="OIDC issuer URL")
    authorization_endpoint: HttpUrl | None = Field(None, description="Authorization endpoint")
    token_endpoint: HttpUrl | None = Field(None, description="Token endpoint")
    userinfo_endpoint: HttpUrl | None = Field(None, description="UserInfo endpoint")
    jwks_uri: HttpUrl | None = Field(None, description="JWKS URI for key validation")
    client_id: str = Field(..., description="Client ID for this application")
    client_secret: str | None = Field(None, description="Client secret (optional if using Vault)")
    client_secret_ref: str | None = Field(None, description="Vault/env reference for client secret")
    redirect_uri: HttpUrl | None = Field(None, description="Redirect URI for callbacks")
    scopes: list[str] = Field(default=["openid", "profile", "email"], description="Requested scopes")
    claim_mapping: dict[str, str] = Field(default_factory=dict, description="OIDC claim to role mapping")
    default_role: str = Field(default="read_only", description="Default role for new users")
    auto_provision_users: bool = Field(default=True, description="Auto-create users on first login")
    enabled: bool = Field(default=True, description="Whether OIDC is enabled")

    class Config:
        extra = "allow"

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> "OIDCProviderConfig | None":
        """Create OIDC config from tenant settings dict.

        Args:
            settings: Tenant settings dictionary containing 'oidc' key

        Returns:
            OIDCProviderConfig instance or None if not configured
        """
        oidc_settings = settings.get("oidc") if settings else None
        if not oidc_settings:
            return None
        if not isinstance(oidc_settings, dict):
            return None
        if not oidc_settings.get("enabled", True):
            return None

        # Handle nested provider-specific config or flat config
        provider_config = oidc_settings.get("config", oidc_settings)

        # Validate required fields
        issuer_url = provider_config.get("issuer_url", "")
        client_id = provider_config.get("client_id", "")

        if not issuer_url:
            raise ValueError("OIDC configuration missing required field: issuer_url")
        if not client_id:
            raise ValueError("OIDC configuration missing required field: client_id")

        return cls(
            provider_name=oidc_settings.get("provider_name", "oidc"),
            issuer_url=issuer_url,
            authorization_endpoint=provider_config.get("authorization_endpoint"),
            token_endpoint=provider_config.get("token_endpoint"),
            userinfo_endpoint=provider_config.get("userinfo_endpoint"),
            jwks_uri=provider_config.get("jwks_uri"),
            client_id=client_id,
            client_secret=provider_config.get("client_secret"),
            client_secret_ref=provider_config.get("client_secret_ref"),
            redirect_uri=provider_config.get("redirect_uri"),
            scopes=provider_config.get("scopes", ["openid", "profile", "email"]),
            claim_mapping=provider_config.get("claim_mapping", {}),
            default_role=provider_config.get("default_role", "read_only"),
            auto_provision_users=provider_config.get("auto_provision_users", True),
            enabled=provider_config.get("enabled", True),
        )
