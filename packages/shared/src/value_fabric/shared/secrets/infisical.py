"""Infisical secrets loader for Value Fabric Platform.

Fetches secrets from Infisical using Universal Auth and injects them into
os.environ *before* pydantic-settings reads them. Falls back gracefully to
existing environment variables when Infisical is not configured.

Required environment variables to enable Infisical:
    INFISICAL_CLIENT_ID       — Universal Auth machine identity client ID
    INFISICAL_CLIENT_SECRET   — Universal Auth machine identity client secret
    INFISICAL_PROJECT_ID      — Infisical project ID
    INFISICAL_ENVIRONMENT     — Environment slug (dev, staging, prod)
    INFISICAL_HOST            — Infisical host URL (default: https://app.infisical.com)
    INFISICAL_SECRET_PATH     — Secret path within project (default: /)
    INFISICAL_OVERWRITE       — If "true", overwrite existing env vars (default: false)

Call load_infisical_secrets() at the earliest point in app startup, before
any Settings() class is instantiated.
"""

import logging
import os
from typing import Optional

from value_fabric.shared.security.config import is_production_like_environment

logger = logging.getLogger(__name__)

REQUIRED_SECRET_KEYS: frozenset[str] = frozenset(
    {
        "JWT_SECRET",
        "DATABASE_URL",
        "API_KEY_HMAC_SECRET",
        "SERVICE_AUTH_SECRET",
    }
)


class InfisicalError(RuntimeError):
    """Base class for Infisical bootstrap failures."""


class InfisicalNotConfiguredError(InfisicalError):
    """Raised when required Infisical bootstrap environment is absent."""


class InfisicalAuthError(InfisicalError):
    """Raised when Universal Auth login fails."""


class InfisicalNetworkError(InfisicalError):
    """Raised when network issues prevent fetching secrets."""


class InfisicalMissingRequiredSecretsError(InfisicalError):
    """Raised when required bootstrap secrets are missing."""


def _raise_or_log(exc: InfisicalError, *, production_like: bool) -> None:
    if production_like:
        raise exc
    logger.warning("%s. Falling back to existing environment variables.", exc)


def _validate_required_secrets() -> None:
    missing = sorted(key for key in REQUIRED_SECRET_KEYS if not os.getenv(key, "").strip())
    if missing:
        raise InfisicalMissingRequiredSecretsError(
            "Missing required secrets: " + ", ".join(missing)
        )


def load_infisical_secrets(
    *,
    project_id: Optional[str] = None,
    environment: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    host: Optional[str] = None,
    secret_path: Optional[str] = None,
    overwrite: Optional[bool] = None,
) -> int:
    """Fetch secrets from Infisical and inject into os.environ.

    All parameters fall back to the corresponding INFISICAL_* environment
    variable when not explicitly provided.

    Args:
        project_id: Infisical project ID (env: INFISICAL_PROJECT_ID).
        environment: Environment slug, e.g. "dev" or "prod"
                     (env: INFISICAL_ENVIRONMENT, default: "dev").
        client_id: Universal Auth client ID (env: INFISICAL_CLIENT_ID).
        client_secret: Universal Auth client secret
                       (env: INFISICAL_CLIENT_SECRET).
        host: Infisical host URL (env: INFISICAL_HOST,
              default: "https://app.infisical.com").
        secret_path: Secret path within the project
                     (env: INFISICAL_SECRET_PATH, default: "/").
        overwrite: When True, overwrite env vars that already exist.
                   When False (default), existing env vars take precedence,
                   allowing local .env overrides during development.
                   (env: INFISICAL_OVERWRITE).

    Returns:
        Number of secrets written into os.environ (0 if not configured).
    """
    production_like = is_production_like_environment(environment)

    client_id = client_id or os.getenv("INFISICAL_CLIENT_ID", "")
    client_secret = client_secret or os.getenv("INFISICAL_CLIENT_SECRET", "")
    project_id = project_id or os.getenv("INFISICAL_PROJECT_ID", "")
    environment = environment or os.getenv("INFISICAL_ENVIRONMENT", "dev")
    host = host or os.getenv("INFISICAL_HOST", "https://app.infisical.com")
    secret_path = secret_path or os.getenv("INFISICAL_SECRET_PATH", "/")

    if overwrite is None:
        overwrite = os.getenv("INFISICAL_OVERWRITE", "false").lower() == "true"

    # All three auth/project fields are required to proceed.
    if not (client_id and client_secret and project_id):
        _raise_or_log(
            InfisicalNotConfiguredError(
                "Infisical not configured: INFISICAL_CLIENT_ID, "
                "INFISICAL_CLIENT_SECRET, and INFISICAL_PROJECT_ID must all be set"
            ),
            production_like=production_like,
        )
        _validate_required_secrets()
        return 0

    try:
        from infisical_sdk import InfisicalSDKClient  # type: ignore[import-untyped]
    except ImportError:
        _raise_or_log(
            InfisicalNotConfiguredError(
                "infisical-sdk is not installed; add dependency before startup"
            ),
            production_like=production_like,
        )
        _validate_required_secrets()
        return 0

    try:
        client = InfisicalSDKClient(host=host)
        try:
            client.auth.universal_auth.login(
                client_id=client_id,
                client_secret=client_secret,
            )
        except Exception as exc:  # noqa: BLE001
            raise InfisicalAuthError(f"Infisical auth failed: {exc}") from exc

        try:
            secrets = client.listSecrets(
                project_id=project_id,
                environment_slug=environment,
                secret_path=secret_path,
                attach_to_process_env=False,
            )
        except Exception as exc:  # noqa: BLE001
            raise InfisicalNetworkError(f"Infisical network/fetch failed: {exc}") from exc

        loaded = 0
        skipped = 0
        for secret in secrets:
            key: str = secret.secret_key
            value: str = secret.secret_value
            if overwrite or key not in os.environ:
                os.environ[key] = value
                loaded += 1
            else:
                skipped += 1

        logger.info(
            "Infisical: loaded %d secrets, skipped %d (already set) "
            "[project=%s, env=%s, path=%s]",
            loaded,
            skipped,
            project_id,
            environment,
            secret_path,
        )
        _validate_required_secrets()
        return loaded

    except InfisicalError as exc:
        _raise_or_log(exc, production_like=production_like)
        _validate_required_secrets()
        return 0

    except Exception as exc:  # noqa: BLE001
        _raise_or_log(
            InfisicalNetworkError(
                "Infisical: unexpected failure while loading secrets; "
                f"check INFISICAL_* configuration and connectivity ({exc})"
            ),
            production_like=production_like,
        )
        _validate_required_secrets()
        return 0
