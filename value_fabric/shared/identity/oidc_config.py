"""Shared OIDC provider configuration model."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OIDCProviderConfig(BaseModel):
    """Tenant-scoped OIDC provider settings."""

    model_config = ConfigDict(extra="allow")

    provider_name: str = "oidc"
    issuer_url: str
    client_id: str
    client_secret_ref: str | None = None
    client_secret: str | None = None
    jwks_uri: str | None = None
    authorization_endpoint: str | None = None
    token_endpoint: str | None = None
    userinfo_endpoint: str | None = None
    redirect_uri: str | None = None
    scopes: list[str] = Field(default_factory=lambda: ["openid", "email", "profile"])
    claim_mapping: dict[str, str] = Field(default_factory=dict)
    default_role: str = "read_only"
    auto_provision_users: bool = False
    enabled: bool = True

    def model_post_init(self, __context: Any) -> None:
        if self.client_secret is not None and self.client_secret_ref is None:
            self.client_secret_ref = self.client_secret

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> "OIDCProviderConfig | None":
        oidc_settings = settings.get("oidc")
        if not oidc_settings:
            return None
        if isinstance(oidc_settings, dict) and "config" in oidc_settings:
            nested = dict(oidc_settings.get("config") or {})
            nested.setdefault("enabled", oidc_settings.get("enabled", True))
            oidc_settings = nested
        if oidc_settings.get("enabled") is False:
            return None
        if not oidc_settings.get("issuer_url"):
            raise ValueError("issuer_url is required for OIDC configuration")
        if not oidc_settings.get("client_id"):
            raise ValueError("client_id is required for OIDC configuration")
        return cls(**oidc_settings)
