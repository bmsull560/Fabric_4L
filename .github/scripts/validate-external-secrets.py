#!/usr/bin/env python3
"""
Validate that all Kubernetes Secret references in layer deployments
are satisfied by ExternalSecret manifests or documented shared secrets.

This script ensures production readiness by failing CI if any layer
references a Secret that won't be populated by the External Secrets Operator.

Exit codes:
    0: All secrets validated successfully
    1: One or more secret references are not satisfied
"""

import sys
from pathlib import Path
from typing import Set, Dict, List
import re

# Shared secrets that are allowed without layer-specific ExternalSecrets
# These are documented shared secrets created by vault-integration.yml
DOCUMENTED_SHARED_SECRETS = {
    "jwt-secret",  # Created by jwt-signing-secret ExternalSecret
    "postgres-secret",  # Created by postgres-password ExternalSecret
    "neo4j-secret",  # Created by neo4j-credentials ExternalSecret
    "redis-secret",  # Not an ExternalSecret but infra-provided
}

# Layer deployment file mappings (layer name -> deployment filename pattern)
LAYER_DEPLOYMENTS = {
    "layer1": "layer1-ingestion.yml",
    "layer2": "layer2-extraction.yml",
    "layer3": "layer3-knowledge.yml",
    "layer4": "layer4-agents.yml",
    "layer5": "layer5-ground-truth.yml",
    "layer6": "layer6-benchmarks.yml",
}


def extract_secret_refs_from_deployment(deployment_path: Path) -> Set[str]:
    """Extract all secret names referenced via secretKeyRef in a deployment file."""
    content = deployment_path.read_text()
    secret_refs = set()

    # Match secretKeyRef patterns
    # Matches: name: <secret-name>
    pattern = r'secretKeyRef:\s*\n\s*name:\s*([\w-]+)'
    matches = re.findall(pattern, content)
    secret_refs.update(matches)

    # Also match secrets referenced in env.valueFrom.configMapKeyRef is NOT a secret
    # Only secretKeyRef counts as a secret reference

    return secret_refs


def extract_external_secret_targets(external_secrets_dir: Path) -> Dict[str, str]:
    """
    Extract all Kubernetes Secret names that will be created by ExternalSecrets.
    Returns dict of secret_name -> source_file
    """
    targets = {}

    # Scan both layer-specific files and vault-integration.yml
    yaml_files = list(external_secrets_dir.glob("*.yaml"))
    vault_integration = external_secrets_dir / "vault-integration.yml"
    if vault_integration.exists():
        yaml_files.append(vault_integration)

    for yaml_file in yaml_files:
        content = yaml_file.read_text()

        # Find target secret names in ExternalSecret manifests
        # Matches: name: <target-secret-name> under target:
        target_pattern = r'target:\s*\n(?:[^\n]*\n)*?\s*name:\s*([\w-]+)'
        matches = re.findall(target_pattern, content)

        for match in matches:
            targets[match] = yaml_file.name

    return targets


def validate_layer(layer_name: str, k8s_dir: Path, external_secret_targets: Dict[str, str]) -> List[str]:
    """
    Validate a single layer's secret references.
    Returns list of error messages (empty if valid).
    """
    errors = []
    deployment_filename = LAYER_DEPLOYMENTS.get(layer_name)
    if not deployment_filename:
        errors.append(f"{layer_name}: No deployment file mapping found")
        return errors

    deployment_file = k8s_dir / deployment_filename

    if not deployment_file.exists():
        errors.append(f"{layer_name}: Deployment file not found: {deployment_file}")
        return errors

    secret_refs = extract_secret_refs_from_deployment(deployment_file)

    if not secret_refs:
        # No secret references - this is valid
        print(f"  {layer_name}: No secret references (OK)")
        return errors

    print(f"  {layer_name}: Found {len(secret_refs)} secret reference(s): {', '.join(sorted(secret_refs))}")

    for secret_name in secret_refs:
        # Check if covered by ExternalSecret
        if secret_name in external_secret_targets:
            print(f"    - {secret_name}: Covered by ExternalSecret ({external_secret_targets[secret_name]})")
            continue

        # Check if documented shared secret
        if secret_name in DOCUMENTED_SHARED_SECRETS:
            print(f"    - {secret_name}: Documented shared secret (OK)")
            continue

        # Not covered - this is an error
        errors.append(
            f"{layer_name}: Secret '{secret_name}' is referenced in deployment "
            f"but not produced by any ExternalSecret or documented as shared"
        )

    return errors


def main() -> int:
    """Main validation entry point."""
    repo_root = Path(__file__).parent.parent.parent
    k8s_dir = repo_root / "k8s"
    external_secrets_dir = k8s_dir / "external-secrets"

    print("=" * 70)
    print("External Secret Validation")
    print("=" * 70)
    print()

    # Step 1: Extract all ExternalSecret targets
    print("Step 1: Scanning ExternalSecret manifests...")
    external_secret_targets = extract_external_secret_targets(external_secrets_dir)
    print(f"  Found {len(external_secret_targets)} secret target(s) from ExternalSecrets:")
    for secret_name, source_file in sorted(external_secret_targets.items()):
        print(f"    - {secret_name} (from {source_file})")
    print()

    # Step 2: Document shared secrets
    print("Step 2: Documented shared secrets (not requiring layer-specific ExternalSecret):")
    for secret_name in sorted(DOCUMENTED_SHARED_SECRETS):
        print(f"    - {secret_name}")
    print()

    # Step 3: Validate each layer
    print("Step 3: Validating layer deployments...")
    all_errors = []

    for layer in sorted(LAYER_DEPLOYMENTS.keys()):
        layer_errors = validate_layer(layer, k8s_dir, external_secret_targets)
        all_errors.extend(layer_errors)

    print()

    # Step 4: Report results
    print("=" * 70)
    if all_errors:
        print(f"FAIL: Found {len(all_errors)} validation error(s)")
        print()
        for error in all_errors:
            print(f"  ERROR: {error}")
        print()
        print("To fix:")
        print("  1. Add an ExternalSecret manifest to k8s/external-secrets/")
        print("  2. Or add the secret to DOCUMENTED_SHARED_SECRETS if it's shared")
        print("  3. Or remove the secret reference from the deployment")
        return 1
    else:
        print("PASS: All secret references are satisfied")
        print()
        print(f"  - All layers validated: {len(LAYER_DEPLOYMENTS)}")
        print(f"  - ExternalSecret coverage: {len(external_secret_targets)} secret(s)")
        print(f"  - Documented shared secrets: {len(DOCUMENTED_SHARED_SECRETS)} secret(s)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
