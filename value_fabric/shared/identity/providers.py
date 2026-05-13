"""OIDC provider resolution helpers.

Provides provider-specific config presets and client secret resolution
for known identity providers (Google, Apple, generic OIDC).
"""

from __future__ import annotations

from value_fabric.shared.identity.oidc_config import OIDCProviderConfig


def resolve_oidc_config(config: OIDCProviderConfig) -> OIDCProviderConfig:
    """Apply provider-specific presets to an OIDC configuration.

    Known presets:
    - google: fills authorization_endpoint, token_endpoint, userinfo_endpoint, scopes
    - apple: fills issuer_url, scopes and sets up JWT-based client secret generation
    """
    provider = (config.provider_name or "oidc").strip().lower()

    if provider == "google":
        return config.model_copy(
            update={
                "authorization_endpoint": config.authorization_endpoint or "https://accounts.google.com/o/oauth2/v2/auth",
                "token_endpoint": config.token_endpoint or "https://oauth2.googleapis.com/token",
                "userinfo_endpoint": config.userinfo_endpoint or "https://openidconnect.googleapis.com/v1/userinfo",
                "scopes": config.scopes or ["openid", "email", "profile"],
            }
        )

    if provider == "apple":
        return config.model_copy(
            update={
                "issuer_url": config.issuer_url or "https://appleid.apple.com",
                "scopes": config.scopes or ["openid", "email", "name"],
            }
        )

    return config


async def resolve_client_secret(config: OIDCProviderConfig) -> str | None:
    """Resolve provider-specific generated client secrets.

    Currently supports Apple Sign In JWT secret generation when
    ``apple_team_id``, ``apple_key_id`` and ``apple_private_key``
    are present in the config.
    """
    provider = (config.provider_name or "oidc").strip().lower()

    if provider == "apple":
        import time

        import jwt

        if not (config.apple_team_id and config.apple_key_id and config.apple_private_key):
            raise ValueError("Apple Sign In requires apple_team_id, apple_key_id and apple_private_key")

        headers = {"kid": config.apple_key_id}
        payload = {
            "iss": config.apple_team_id,
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400,
            "aud": "https://appleid.apple.com",
            "sub": config.client_id,
        }
        return jwt.encode(payload, config.apple_private_key.replace("\\n", "\n"), algorithm="ES256", headers=headers)

    return None
