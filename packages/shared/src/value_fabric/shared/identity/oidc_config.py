"""OIDC provider configuration model."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator

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

    @field_validator("issuer_url", "client_id")
    @classmethod
    def _required_non_empty(cls, value: str, info) -> str:
        if not value or not value.strip():
            raise ValueError(f"{info.field_name} is required")
        return value.strip()

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

        if oidc_settings.get("enabled") is False:
            return None

        config = oidc_settings.get("config")
        if isinstance(config, dict):
            provider_config = dict(config)
            provider_config.setdefault("provider_name", oidc_settings.get("provider_name", "oidc"))
            provider_config["enabled"] = oidc_settings.get("enabled", True)
            if "scopes" in oidc_settings and "scopes" not in provider_config:
                provider_config["scopes"] = oidc_settings["scopes"]
            if "claim_mapping" in oidc_settings and "claim_mapping" not in provider_config:
                provider_config["claim_mapping"] = oidc_settings["claim_mapping"]
            if "default_role" in oidc_settings and "default_role" not in provider_config:
                provider_config["default_role"] = oidc_settings["default_role"]
            if "auto_provision_users" in oidc_settings and "auto_provision_users" not in provider_config:
                provider_config["auto_provision_users"] = oidc_settings["auto_provision_users"]
        else:
            provider_config = dict(oidc_settings)
            provider_config.setdefault("provider_name", "oidc")

        try:
            return cls.model_validate(provider_config)
        except ValidationError as exc:
            logger.exception("OIDC configuration validation failed")
            missing_fields = [
                ".".join(str(part) for part in error["loc"])
                for error in exc.errors()
                if error.get("type") == "missing"
            ]
            if missing_fields:
                raise ValueError(
                    f"OIDC configuration missing required field(s): {', '.join(missing_fields)}"
                ) from exc
            raise ValueError(f"OIDC configuration validation failed: {exc}") from exc
