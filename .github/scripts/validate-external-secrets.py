#!/usr/bin/env python3
"""
Validate that all Kubernetes Secret references in layer deployments
are satisfied by ExternalSecret manifests or documented shared secrets.

This script ensures production readiness by failing CI if any layer
references a Secret that won't be populated by the External Secrets Operator.

Uses PyYAML for robust parsing instead of regex to avoid injection attacks
and correctly handle YAML edge cases (comments, multiline, nested structures).

Exit codes:
    0: All secrets validated successfully
    1: One or more secret references are not satisfied
"""

import sys
from pathlib import Path
from typing import Set, Dict, List, Any, Optional
import os

# Use PyYAML for robust YAML parsing
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install: pip install pyyaml")
    sys.exit(1)

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
    """
    Extract all secret names referenced via secretKeyRef in a deployment file.
    
    Uses PyYAML for robust parsing that correctly handles:
    - Normal mappings
    - Nested lists
    - Varied whitespace
    - Comments
    - Multiline YAML
    - Flow style (inline) and block style
    """
    secret_refs = set()
    
    try:
        # Load all documents from the YAML file
        with open(deployment_path, 'r', encoding='utf-8') as f:
            documents = list(yaml.safe_load_all(f))
    except yaml.YAMLError as e:
        print(f"WARNING: Failed to parse {deployment_path}: {e}")
        return secret_refs
    except Exception as e:
        print(f"WARNING: Error reading {deployment_path}: {e}")
        return secret_refs
    
    for doc in documents:
        if not doc or not isinstance(doc, dict):
            continue
        
        # Recursively search for secretKeyRef in the document
        secret_refs.update(_find_secret_refs_recursive(doc))
    
    return secret_refs


def _find_secret_refs_recursive(obj: Any, path: str = "") -> Set[str]:
    """Recursively find all secretKeyRef.name values in a nested structure."""
    secret_refs = set()
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            
            # Check if this is a secretKeyRef structure
            if key == "secretKeyRef" and isinstance(value, dict):
                secret_name = value.get("name")
                if secret_name and isinstance(secret_name, str):
                    secret_refs.add(secret_name)
            # Also check for { secretKeyRef: { name: ... } } pattern
            elif key == "valueFrom" and isinstance(value, dict):
                if "secretKeyRef" in value:
                    secret_ref = value["secretKeyRef"]
                    if isinstance(secret_ref, dict):
                        secret_name = secret_ref.get("name")
                        if secret_name and isinstance(secret_name, str):
                            secret_refs.add(secret_name)
            # Continue recursion for nested structures
            else:
                secret_refs.update(_find_secret_refs_recursive(value, current_path))
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            secret_refs.update(_find_secret_refs_recursive(item, f"{path}[{i}]"))
    
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
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                documents = list(yaml.safe_load_all(f))
        except yaml.YAMLError as e:
            print(f"WARNING: Failed to parse {yaml_file}: {e}")
            continue
        except Exception as e:
            print(f"WARNING: Error reading {yaml_file}: {e}")
            continue
        
        for doc in documents:
            if not doc or not isinstance(doc, dict):
                continue
            
            # Check if this is an ExternalSecret document
            if doc.get("kind") != "ExternalSecret":
                continue
            
            # Extract target secret name
            spec = doc.get("spec", {})
            target = spec.get("target", {})
            
            # Handle both dict and None cases
            if isinstance(target, dict):
                secret_name = target.get("name")
                if secret_name and isinstance(secret_name, str):
                    targets[secret_name] = yaml_file.name
    
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


def run_self_tests() -> bool:
    """
    Run self-tests to validate the script's functionality.
    
    These tests help detect if the script has been maliciously modified
    to always pass or bypass validation.
    
    Returns True if all tests pass.
    """
    print("Running self-tests...")
    test_failures = []
    
    # Test 1: _find_secret_refs_recursive finds secrets correctly
    test_doc = {
        "spec": {
            "containers": [{
                "env": [{
                    "valueFrom": {
                        "secretKeyRef": {"name": "test-secret-1", "key": "password"}
                    }
                }]
            }]
        }
    }
    result = _find_secret_refs_recursive(test_doc)
    if "test-secret-1" not in result:
        test_failures.append("_find_secret_refs_recursive failed to find nested secret")
    
    # Test 2: Empty document returns empty set
    empty_result = _find_secret_refs_recursive({})
    if empty_result:
        test_failures.append("_find_secret_refs_recursive should return empty set for empty doc")
    
    # Test 3: Multiple secrets found
    multi_doc = {
        "spec": {
            "initContainers": [{
                "env": [{
                    "valueFrom": {
                        "secretKeyRef": {"name": "init-secret", "key": "key1"}
                    }
                }]
            }],
            "containers": [{
                "env": [{
                    "valueFrom": {
                        "secretKeyRef": {"name": "main-secret", "key": "key2"}
                    }
                }]
            }]
        }
    }
    multi_result = _find_secret_refs_recursive(multi_doc)
    if "init-secret" not in multi_result or "main-secret" not in multi_result:
        test_failures.append("_find_secret_refs_recursive failed to find multiple secrets")
    
    # Report results
    if test_failures:
        print("SELF-TEST FAILURES:")
        for failure in test_failures:
            print(f"  - {failure}")
        return False
    
    print("Self-tests passed.")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate ExternalSecret coverage")
    parser.add_argument("--self-test", action="store_true", help="Run self-tests and exit")
    args = parser.parse_args()
    
    if args.self_test:
        success = run_self_tests()
        sys.exit(0 if success else 1)
    
    sys.exit(main())
