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

logger = logging.getLogger(__name__)


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
        logger.debug(
            "Infisical not configured — INFISICAL_CLIENT_ID, INFISICAL_CLIENT_SECRET, "
            "and INFISICAL_PROJECT_ID must all be set. "
            "Falling back to existing environment variables."
        )
        return 0

    try:
        from infisical_sdk import InfisicalSDKClient  # type: ignore[import-untyped]
    except ImportError:
        logger.warning(
            "infisical-sdk is not installed. "
            "Add it to your dependencies and re-build the image. "
            "Falling back to existing environment variables."
        )
        return 0

    try:
        client = InfisicalSDKClient(host=host)
        client.auth.universal_auth.login(
            client_id=client_id,
            client_secret=client_secret,
        )

        secrets = client.listSecrets(
            project_id=project_id,
            environment_slug=environment,
            secret_path=secret_path,
            attach_to_process_env=False,
        )

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
        return loaded

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Infisical: failed to load secrets — %s. "
            "Service will start with existing environment variables only. "
            "Check INFISICAL_* configuration and network connectivity.",
            exc,
        )
        return 0
