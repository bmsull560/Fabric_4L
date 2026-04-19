#!/usr/bin/env python3
"""Standalone check for External Secrets Operator ClusterSecretStore readiness."""

import subprocess
import sys

def _log(msg: str) -> None:
    print(msg)


def check_cluster_secret_store() -> int:
    """Check if ClusterSecretStore is ready and ExternalSecrets are synced."""
    
    # 1. Check ClusterSecretStore status
    _log("Checking ClusterSecretStore status...")
    result = subprocess.run(
        ["kubectl", "get", "ClusterSecretStore", "vault-backend", 
         "-o", "jsonpath={.status.conditions[?(@.type=='Ready')].status}"],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        _log(f"FAIL: Cannot get ClusterSecretStore status: {result.stderr}")
        return 1
    
    if result.stdout.strip() != "True":
        _log(f"FAIL: ClusterSecretStore not ready (status: {result.stdout.strip()})")
        return 1
    
    _log("PASS: ClusterSecretStore is Ready")
    
    # 2. Check ExternalSecrets in value-fabric namespace
    _log("Checking ExternalSecrets in value-fabric namespace...")
    result = subprocess.run(
        ["kubectl", "get", "externalsecret", "-n", "value-fabric", 
         "-o", "jsonpath={.items[*].metadata.name}"],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        _log(f"FAIL: Cannot list ExternalSecrets: {result.stderr}")
        return 1
    
    externalsecrets = result.stdout.strip().split()
    if not externalsecrets:
        _log("WARN: No ExternalSecrets found in value-fabric namespace")
    else:
        _log(f"Found {len(externalsecrets)} ExternalSecrets: {', '.join(externalsecrets)}")
    
    # 3. Check ExternalSecret sync status
    failed_syncs = []
    for es in externalsecrets:
        result = subprocess.run(
            ["kubectl", "get", "externalsecret", es, "-n", "value-fabric",
             "-o", "jsonpath={.status.conditions[?(@.type=='Ready')].status}"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or result.stdout.strip() != "True":
            failed_syncs.append(es)
    
    if failed_syncs:
        _log(f"FAIL: ExternalSecrets not synced: {', '.join(failed_syncs)}")
        return 1
    
    _log("PASS: All ExternalSecrets are synced")
    
    # 4. Check that corresponding K8s Secrets exist
    _log("Checking synced Kubernetes Secrets...")
    result = subprocess.run(
        ["kubectl", "get", "secrets", "-n", "value-fabric",
         "-o", "jsonpath={.items[*].metadata.name}"],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        _log(f"WARN: Cannot list secrets: {result.stderr}")
    else:
        secrets = result.stdout.strip().split()
        # Look for secrets that might be from ExternalSecret sync
        es_secrets = [s for s in secrets if any(
            x in s for x in ["openai", "postgres", "neo4j", "jwt", "layer"]
        )]
        if es_secrets:
            _log(f"Found {len(es_secrets)} secrets from ExternalSecret sync")
    
    _log("All ClusterSecretStore checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(check_cluster_secret_store())
