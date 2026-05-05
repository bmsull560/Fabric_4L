"""OIDC provider configuration model."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class OIDCProviderConfig(BaseModel):
    """Configuration for an external OIDC identity provider."""

    provider_name: str = Field(..., description="Human-readable provider name")
    issuer_url: str = Field(..., description="OIDC issuer URL")
    client_id: str = Field(..., description="OAuth2 client ID")
    client_secret_ref: Optional[str] = Field(
        None, description="Reference to the client secret (e.g., env var or vault path)"
    )
    scopes: List[str] = Field(default_factory=lambda: ["openid", "email", "profile"])
    claim_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from claim values to VF Role (e.g., {'admin': 'tenant_admin'})",
    )
    default_role: str = Field("read_only", description="Fallback role when no claim mapping matches")
    auto_provision_users: bool = Field(False, description="Create users automatically on first login")
    enabled: bool = Field(True, description="Whether this provider is active")

    @classmethod
    def from_settings(cls, settings: dict) -> "OIDCProviderConfig | None":
        """Parse OIDC provider config from tenant settings dict.

        Expected settings shape:
            {
                "oidc": {
                    "provider_name": "...",
                    "issuer_url": "...",
                    "client_id": "...",
                    ...
                }
            }
        """
        oidc_settings = settings.get("oidc") if settings else None
        if not isinstance(oidc_settings, dict):
            return None
        try:
            return cls.model_validate(oidc_settings)
        except Exception:
            logger.exception("OIDC configuration validation failed")
            return None
