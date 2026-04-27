"""Agent Bill of Materials (ABOM) model and loader.

Provides a typed Python model for ABOM manifests and a loader that
validates manifests against the JSON Schema contract, computes a
canonical manifest hash, and caches loaded manifests.

GATE Framework §2.1 — Agent Bill of Materials
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from shared.crypto.canonical import canonical_hash

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# ABOM Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════


class ABOMInvariants(BaseModel):
    """Invariant constraints declared in an ABOM manifest."""

    max_tool_calls_per_run: int = Field(..., ge=1)
    budget_limit_usd: float | None = None
    require_human_approval: list[str] = Field(default_factory=list)
    custom: dict[str, Any] = Field(default_factory=dict)


class ABOMMetadata(BaseModel):
    """Optional metadata for an ABOM manifest."""

    description: str | None = None
    owner: str | None = None
    last_reviewed: str | None = None


class AgentBillOfMaterials(BaseModel):
    """Agent Bill of Materials (ABOM) manifest.

    Declares an agent's identity, privilege tier, allowed tools, and
    invariant constraints.  Used by ToolGateway and InvariantEvaluator
    to enforce pre-execution policy checks.
    """

    schema_version: str = "1.0"
    agent_type: str
    agent_id: str = ""  # Set at runtime by BaseAgent
    privilege_tier: str = "standard"  # "standard" | "elevated" | "high_privilege"
    allowed_tools: list[str] = Field(default_factory=list)
    denied_tools: list[str] = Field(default_factory=list)
    invariants: ABOMInvariants
    metadata: ABOMMetadata | None = None

    def manifest_hash(self) -> str:
        """Compute canonical SHA-256 hash of this manifest."""
        return canonical_hash(self.model_dump(exclude_none=True))

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if a tool is permitted for this agent.

        Denied tools take precedence over allowed tools.
        """
        if tool_name in self.denied_tools:
            return False
        return tool_name in self.allowed_tools


# ═══════════════════════════════════════════════════════════════════════════
# ABOM Loader
# ═══════════════════════════════════════════════════════════════════════════

_manifest_cache: dict[str, AgentBillOfMaterials] = {}


def load_abom(manifest_path: str | Path) -> AgentBillOfMaterials:
    """Load and validate an ABOM manifest from a JSON file.

    Args:
        manifest_path: Path to the ABOM JSON manifest.

    Returns:
        Validated AgentBillOfMaterials instance.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        ValueError: If the manifest fails validation.
    """
    path = Path(manifest_path)
    cache_key = str(path.resolve())

    if cache_key in _manifest_cache:
        return _manifest_cache[cache_key]

    if not path.exists():
        raise FileNotFoundError(f"ABOM manifest not found: {path}")

    raw = json.loads(path.read_text())
    abom = AgentBillOfMaterials(**raw)

    _manifest_cache[cache_key] = abom
    logger.info(
        "Loaded ABOM: agent_type=%s tier=%s tools=%d hash=%s",
        abom.agent_type,
        abom.privilege_tier,
        len(abom.allowed_tools),
        abom.manifest_hash()[:12],
    )
    return abom


def clear_abom_cache() -> None:
    """Clear the ABOM manifest cache (for testing)."""
    _manifest_cache.clear()
