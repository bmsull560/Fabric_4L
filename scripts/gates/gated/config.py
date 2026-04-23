"""Daemon configuration."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class DaemonConfig(BaseModel):
    """Gate daemon configuration."""
    
    bind_addr: str = Field(default="0.0.0.0")
    port: int = Field(default=8888)
    log_level: str = Field(default="INFO")
    max_concurrent_gates: int = Field(default=5)
    artifact_store: str = Field(default="./artifacts")
    
    # Plugin configuration
    plugin_search_path: list[str] = Field(default_factory=lambda: [
        "scripts/gates/plugins",
        "packs/*/gates",
    ])
    
    # Tracing
    tracing_enabled: bool = Field(default=True)
    tracing_endpoint: Optional[str] = Field(default=None)
    
    # Policy
    policy_file: Path = Field(default=Path(".fabric/prod-gates.policy.yaml"))
    
    class Config:
        env_prefix = "GATED_"
