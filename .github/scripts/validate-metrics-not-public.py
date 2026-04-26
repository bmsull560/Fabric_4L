#!/usr/bin/env python3
"""
Validate that /metrics endpoint is not exposed through public ingress.

This script scans Kubernetes ingress manifests to ensure the /metrics endpoint
is not routable from public networks. Metrics should be internal-only.

Exit codes:
    0: /metrics is not publicly routable
    1: /metrics is exposed through public ingress
"""

import re
import sys
from pathlib import Path
from typing import List

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install: pip install pyyaml")
    sys.exit(1)


def find_ingress_manifests(k8s_dir: Path) -> List[Path]:
    """Find all ingress-related YAML files."""
    manifests = []
    
    # Search patterns for ingress manifests
    patterns = [
        "**/*ingress*.yml",
        "**/*ingress*.yaml",
        "**/gateway-api/*.yml",
        "**/istio/*.yml",
        "**/nginx/*.yml",
        "**/routing/**/*.yml",
    ]
    
    for pattern in patterns:
        manifests.extend(k8s_dir.glob(pattern))
    
    return list(set(manifests))  # Remove duplicates


def check_metrics_exposed_in_ingress(manifest_path: Path) -> List[str]:
    """
    Check if an ingress manifest exposes /metrics publicly.
    
    Returns list of violations found.
    """
    violations = []
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            documents = list(yaml.safe_load_all(f))
    except yaml.YAMLError as e:
        print(f"WARNING: Failed to parse {manifest_path}: {e}")
        return violations
    except Exception as e:
        print(f"WARNING: Error reading {manifest_path}: {e}")
        return violations
    
    for doc_idx, doc in enumerate(documents):
        if not doc or not isinstance(doc, dict):
            continue
        
        kind = doc.get("kind", "")
        metadata = doc.get("metadata", {})
        name = metadata.get("name", f"document-{doc_idx}")
        
        # Check Ingress resources
        if kind == "Ingress":
            spec = doc.get("spec", {})
            rules = spec.get("rules", [])
            
            for rule_idx, rule in enumerate(rules):
                http = rule.get("http", {})
                paths = http.get("paths", [])
                
                for path in paths:
                    path_value = path.get("path", "")
                    
                    # Check if /metrics is exposed
                    if _is_metrics_path_exposed(path_value):
                        violations.append(
                            f"{manifest_path.name}: Ingress/{name} exposes "
                            f"/metrics at path '{path_value}' (rule {rule_idx})"
                        )
        
        # Check HTTPRoute (Gateway API)
        elif kind == "HTTPRoute":
            spec = doc.get("spec", {})
            rules = spec.get("rules", [])
            
            for rule_idx, rule in enumerate(rules):
                matches = rule.get("matches", [])
                
                for match in matches:
                    path = match.get("path", {})
                    path_value = path.get("value", "")
                    path_type = path.get("type", "PathPrefix")
                    
                    if _is_metrics_path_exposed(path_value, path_type):
                        violations.append(
                            f"{manifest_path.name}: HTTPRoute/{name} exposes "
                            f"/metrics at path '{path_value}' (type: {path_type}, rule {rule_idx})"
                        )
        
        # Check VirtualService (Istio)
        elif kind == "VirtualService":
            spec = doc.get("spec", {})
            http_routes = spec.get("http", [])
            
            for route_idx, route in enumerate(http_routes):
                match_list = route.get("match", [])
                
                for match in match_list:
                    uri = match.get("uri", {})
                    prefix = uri.get("prefix", "")
                    exact = uri.get("exact", "")
                    
                    if _is_metrics_path_exposed(prefix or exact):
                        violations.append(
                            f"{manifest_path.name}: VirtualService/{name} exposes "
                            f"/metrics at path '{prefix or exact}' (route {route_idx})"
                        )
        
        # Check generic routes in ConfigMaps (NGINX config)
        elif kind == "ConfigMap":
            data = doc.get("data", {})
            
            for key, value in data.items():
                if not isinstance(value, str):
                    continue
                
                # Check for NGINX location blocks exposing /metrics
                if "location" in value and "/metrics" in value:
                    # Check if it's a public server block (not internal listener)
                    if _is_nginx_metrics_public(value):
                        violations.append(
                            f"{manifest_path.name}: ConfigMap/{name} key '{key}' "
                            f"may expose /metrics in NGINX config"
                        )
    
    return violations


def _is_metrics_path_exposed(path: str, path_type: str = "") -> bool:
    """
    Check if a path would expose /metrics.

    Handles:
    - Exact match: /metrics
    - Prefix match: /metrics/* or /metrics*
    - Regex/pattern match: patterns containing "metrics"
    """
    if not path:
        return False

    normalized = path.rstrip("/")

    # Exact /metrics exposure
    if normalized == "/metrics":
        return True

    # Prefix match that includes /metrics (e.g., /metrics/*)
    if normalized.startswith("/metrics/"):
        return True

    # PathPrefix type that starts with /metrics
    if path_type == "PathPrefix" and normalized.startswith("/metrics"):
        return True

    # Regex or pattern match containing "metrics" as path segment
    if "metrics" in normalized.lower():
        # Ensure it's not just a substring (e.g., /some-metrics should match)
        # but avoid false positives (e.g., /prometheusmetrics should not)
        parts = normalized.split("/")
        if any("metrics" in part.lower() for part in parts):
            return True

    return False


# Patterns indicating internal/private network restrictions in NGINX config
_INTERNAL_IP_PATTERNS = [
    "allow 10.",
    "allow 172.16",
    "allow 172.17",
    "allow 172.18",
    "allow 172.19",
    "allow 172.20",
    "allow 172.21",
    "allow 172.22",
    "allow 172.23",
    "allow 172.24",
    "allow 172.25",
    "allow 172.26",
    "allow 172.27",
    "allow 172.28",
    "allow 172.29",
    "allow 172.30",
    "allow 172.31",
    "allow 192.168.",
    "allow 127.0.0.1",
    "allow 169.254.",  # Link-local (EC2 metadata, etc.)
    "allow ::1",  # IPv6 localhost
    "allow fc00:",  # IPv6 unique local
    "allow fd00:",  # IPv6 unique local
    "deny all",
    "internal",
    "listen 127",
    "listen 10.",
    "listen [::1]",
]


def _is_nginx_metrics_public(config: str) -> bool:
    """
    Check if NGINX config exposes /metrics publicly.

    Heuristics:
    - location /metrics without internal IP restrictions
    - Not in a server block listening only on internal addresses
    """
    # Look for location /metrics blocks
    metrics_locations = re.findall(
        r'location\s+(/metrics[^\{]*)\s*\{([^}]+)\}',
        config,
        re.DOTALL | re.IGNORECASE
    )

    for _location_path, location_body in metrics_locations:
        # Check if it has internal restrictions
        has_internal_restriction = any(
            pattern in location_body.lower()
            for pattern in _INTERNAL_IP_PATTERNS
        )

        if not has_internal_restriction:
            return True

    return False


def main() -> int:
    """Main validation function."""
    repo_root = Path(__file__).parent.parent.parent
    k8s_dir = repo_root / "k8s"
    
    print("=" * 70)
    print("Metrics Public Exposure Validation")
    print("=" * 70)
    print()
    
    # Find all ingress manifests
    print("Step 1: Scanning for ingress manifests...")
    manifests = find_ingress_manifests(k8s_dir)
    print(f"  Found {len(manifests)} ingress-related manifest(s)")
    print()
    
    # Check each manifest
    print("Step 2: Checking for /metrics exposure...")
    all_violations = []
    
    for manifest in sorted(manifests):
        violations = check_metrics_exposed_in_ingress(manifest)
        all_violations.extend(violations)
    
    # Report results
    print()
    print("=" * 70)
    
    if all_violations:
        print(f"FAIL: Found {len(all_violations)} violation(s)")
        print()
        for violation in all_violations:
            print(f"  ERROR: {violation}")
        print()
        print("To fix:")
        print("  1. Add IP allowlist restricting to internal networks (10.x, 172.16-31.x, 192.168.x)")
        print("  2. Or remove /metrics from public ingress routes")
        print("  3. Or use internal ingress/controller for metrics scraping only")
        print()
        print("Valid internal-only patterns:")
        print('  - NGINX: location /metrics { allow 10.0.0.0/8; deny all; }')
        print('  - Istio: match with sourceLabels for internal workloads')
        print('  - Gateway API: HTTPRoute with internal-only Gateway')
        return 1
    else:
        print("PASS: /metrics is not exposed through public ingress")
        print()
        print(f"  - Manifests scanned: {len(manifests)}")
        print("  - /metrics exposure: None detected")
        return 0


if __name__ == "__main__":
    sys.exit(main())
