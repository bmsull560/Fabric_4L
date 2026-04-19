"""OIDC provider configuration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class OIDCProviderConfig(BaseModel):
    """Configuration for an OIDC provider."""

    issuer: str = Field(..., description="OIDC issuer URL")
    authorization_endpoint: HttpUrl = Field(..., description="Authorization endpoint")
    token_endpoint: HttpUrl = Field(..., description="Token endpoint")
    userinfo_endpoint: HttpUrl | None = Field(None, description="UserInfo endpoint")
    jwks_uri: HttpUrl | None = Field(None, description="JWKS URI for key validation")
    client_id: str = Field(..., description="Client ID for this application")
    client_secret: str = Field(..., description="Client secret")
    redirect_uri: HttpUrl = Field(..., description="Redirect URI for callbacks")
    scopes: list[str] = Field(default=["openid", "profile", "email"], description="Requested scopes")
    
    class Config:
        extra = "allow"
