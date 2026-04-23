"""Policy loader from YAML."""

import logging
from pathlib import Path
from typing import Optional

import yaml

from .models import Comparator, GatePolicy, GateSeverity, PolicyConfig, PolicyThreshold


class PolicyLoader:
    """Loads policy from YAML files."""
    
    def __init__(self):
        self.logger = logging.getLogger("gated.policy")
    
    def load(self, path: Path) -> Optional[PolicyConfig]:
        """Load policy from YAML file."""
        if not path.exists():
            self.logger.warning(f"Policy file not found: {path}")
            return None
        
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            
            return self._parse_config(data)
        
        except Exception as e:
            self.logger.error(f"Failed to load policy: {e}")
            return None
    
    def _parse_config(self, data: dict) -> PolicyConfig:
        """Parse policy configuration from dict."""
        config = PolicyConfig(
            version=data.get("version", "1.0"),
            enforcement_mode=data.get("enforcement_mode", "fail-closed"),
            block_on_missing_artifacts=data.get("block_on_missing_artifacts", True),
        )
        
        # Parse stale gate results
        if "stale_gate_results" in data:
            config.stale_gate_results = data["stale_gate_results"]
        
        # Parse gates
        gates_data = data.get("gates", {})
        for gate_id, gate_data in gates_data.items():
            gate_policy = self._parse_gate(gate_id, gate_data)
            config.gates.append(gate_policy)
        
        # Parse profiles
        config.profiles = data.get("profiles", {})
        
        return config
    
    def _parse_gate(self, gate_id: str, data: dict) -> GatePolicy:
        """Parse a single gate policy."""
        severity = GateSeverity(data.get("severity", "warning"))
        
        # Parse checks
        checks = []
        for check_data in data.get("checks", []):
            threshold = PolicyThreshold(
                name=check_data.get("name", "unknown"),
                expected=check_data.get("expected"),
                comparator=check_data.get("comparator", "eq"),
                max_allowed_failures=check_data.get("max_allowed_failures", 0),
            )
            checks.append(threshold)
        
        # Get enabled profiles from matrix
        enabled_profiles = []
        if "matrix" in data:
            for profile, settings in data["matrix"].items():
                if settings.get("enabled", False):
                    enabled_profiles.append(profile)
        
        return GatePolicy(
            gate_id=gate_id,
            severity=severity,
            owner=data.get("owner", "unknown"),
            description=data.get("description", ""),
            checks=checks,
            artifacts=data.get("artifacts", []),
            fail_on_error=data.get("fail_on_error", True),
            max_allowed_failures=data.get("max_allowed_failures", 0),
            enabled_profiles=enabled_profiles,
        )
