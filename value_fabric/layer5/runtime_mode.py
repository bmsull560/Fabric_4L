"""Runtime mode helpers shared across config and auth policy checks."""

PRODUCTION_LIKE_ENVIRONMENTS = {"production", "prod", "staging", "stage"}


def normalize_environment(value: str | None) -> str:
    """Normalize an environment name for runtime policy decisions."""
    return (value or "development").strip().lower()


def is_production_like_mode(environment: str | None, app_env: str | None = None) -> bool:
    """Return whether effective runtime mode must enforce production fail-closed auth."""
    effective_environment = normalize_environment(app_env or environment)
    return effective_environment in PRODUCTION_LIKE_ENVIRONMENTS

