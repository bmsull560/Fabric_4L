#!/usr/bin/env python3
"""
Validate Production Gates Policy Schema

Validates the structure and content of the prod-gates.policy.yaml file
to ensure all required gates and profiles are properly configured.

Exit codes:
- 0: Policy is valid
- 1: Policy validation failed
- 2: Schema/file error
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# Schema for valid policy structure
POLICY_SCHEMA = {
    "required_top_level": ["version", "gates", "profiles"],
    "required_gate_fields": ["enabled", "description", "thresholds"],
    "required_thresholds": ["pr-fast", "mainline-full", "release-candidate"],
    "valid_profiles": ["pr-fast", "mainline-full", "release-candidate"],
    "known_gates": [
        "contract",
        "arch",
        "security",
        "chaos",
        "smoke",
        "agent",
        "state",
        "obs",
        "release-policy",
    ],
}


class PolicyValidator:
    """Validates the production gates policy file."""

    def __init__(self, policy_file: str):
        self.policy_file = Path(policy_file)
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """Run all validation checks. Returns True if valid."""
        print(f"🔍 Validating policy file: {self.policy_file}")

        # Check file exists
        if not self.policy_file.exists():
            self.errors.append(f"Policy file not found: {self.policy_file}")
            return False

        # Load policy
        try:
            policy = self._load_policy()
        except Exception as e:
            self.errors.append(f"Failed to load policy: {e}")
            return False

        # Run validations
        self._validate_top_level_structure(policy)
        self._validate_version(policy)
        self._validate_gates(policy)
        self._validate_profiles(policy)
        self._validate_references(policy)

        # Report results
        self._print_results()

        return len(self.errors) == 0

    def _load_policy(self) -> Dict[str, Any]:
        """Load policy from YAML or JSON."""
        import yaml
        with open(self.policy_file, "r") as f:
            return yaml.safe_load(f)

    def _validate_top_level_structure(self, policy: Dict[str, Any]) -> None:
        """Validate top-level keys exist."""
        for key in POLICY_SCHEMA["required_top_level"]:
            if key not in policy:
                self.errors.append(f"Missing required top-level key: '{key}'")

    def _validate_version(self, policy: Dict[str, Any]) -> None:
        """Validate version format."""
        version = policy.get("version", "")
        if not version:
            self.errors.append("Missing or empty 'version' field")
            return

        # Should be semver-like
        parts = version.split(".")
        if len(parts) < 2:
            self.errors.append(f"Invalid version format: '{version}' (expected x.y.z)")

    def _validate_gates(self, policy: Dict[str, Any]) -> None:
        """Validate gates section."""
        gates = policy.get("gates", {})
        if not gates:
            self.errors.append("'gates' section is empty or missing")
            return

        for gate_name, gate_config in gates.items():
            # Check for unknown gates
            if gate_name not in POLICY_SCHEMA["known_gates"]:
                self.warnings.append(f"Unknown gate: '{gate_name}' (may be new)")

            # Check required fields
            for field in POLICY_SCHEMA["required_gate_fields"]:
                if field not in gate_config:
                    self.errors.append(f"Gate '{gate_name}' missing required field: '{field}'")

            # Validate thresholds if present
            thresholds = gate_config.get("thresholds", {})
            if thresholds:
                for profile in POLICY_SCHEMA["required_thresholds"]:
                    if profile not in thresholds:
                        self.errors.append(f"Gate '{gate_name}' missing threshold for profile: '{profile}'")

    def _validate_profiles(self, policy: Dict[str, Any]) -> None:
        """Validate profiles section."""
        profiles = policy.get("profiles", {})
        if not profiles:
            self.errors.append("'profiles' section is empty or missing")
            return

        for profile_name in profiles.keys():
            if profile_name not in POLICY_SCHEMA["valid_profiles"]:
                self.errors.append(f"Invalid profile name: '{profile_name}'")

        # Check all required profiles exist
        for required in POLICY_SCHEMA["valid_profiles"]:
            if required not in profiles:
                self.errors.append(f"Missing required profile: '{required}'")

    def _validate_references(self, policy: Dict[str, Any]) -> None:
        """Validate cross-references between gates and profiles."""
        gates = policy.get("gates", {})
        profiles = policy.get("profiles", {})

        # Check that gates referenced in profiles exist
        for profile_name, profile_config in profiles.items():
            enabled_gates = profile_config.get("enabled_gates", [])
            for gate in enabled_gates:
                if gate not in gates:
                    self.errors.append(f"Profile '{profile_name}' references unknown gate: '{gate}'")

    def _print_results(self) -> None:
        """Print validation results."""
        print()

        if self.warnings:
            print("⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()

        if self.errors:
            print("❌ Errors:")
            for error in self.errors:
                print(f"  • {error}")
            print()
            print(f"Validation FAILED: {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
        else:
            print(f"✅ Policy is valid ({len(self.warnings)} warning(s))")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate production gates policy file",
    )
    parser.add_argument(
        "--policy",
        required=True,
        help="Path to the policy YAML file",
    )

    args = parser.parse_args()

    validator = PolicyValidator(args.policy)
    valid = validator.validate()

    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
