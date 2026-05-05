"""Neo4j production configuration guardrails."""

from __future__ import annotations

from urllib.parse import urlparse


PRODUCTION_LIKE_ENVIRONMENTS = {"production", "prod", "staging", "stage"}
INSECURE_NEO4J_PASSWORDS = {"", "password", "neo4j", "valuefabric", "test", "test-password"}


def is_production_like_environment(environment: str | None) -> bool:
    """Return whether an environment name should fail closed."""
    return (environment or "").strip().lower() in PRODUCTION_LIKE_ENVIRONMENTS


def validate_neo4j_aura_config(
    *,
    uri: str | None,
    password: str | None,
    environment: str | None,
) -> None:
    """Require managed Neo4j Aura wiring in production-like environments."""
    if not is_production_like_environment(environment):
        return

    parsed = urlparse(uri or "")
    host = (parsed.hostname or "").lower()
    scheme = (parsed.scheme or "").lower()
    password_value = (password or "").strip()

    if scheme != "neo4j+s":
        raise ValueError(
            "NEO4J_URI must use neo4j+s:// Aura routing in production/staging."
        )
    if not host or host in {"localhost", "127.0.0.1", "neo4j"} or host.endswith(".svc"):
        raise ValueError(
            "NEO4J_URI must point to managed Neo4j Aura, not localhost or in-cluster Neo4j."
        )
    if password_value.lower() in INSECURE_NEO4J_PASSWORDS:
        raise ValueError("NEO4J_PASSWORD must be a strong non-default secret.")
