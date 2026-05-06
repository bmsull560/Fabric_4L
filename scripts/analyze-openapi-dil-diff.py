#!/usr/bin/env python3
"""
Analyze OpenAPI ↔ DIL hook coverage

This script compares OpenAPI endpoint specifications with frontend DIL hooks
to identify coverage gaps.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Paths
CONTRACTS_DIR = Path("contracts/openapi")
HOOKS_DIR = Path("apps/web/src/hooks")

# Expected DIL services based on FRONTEND_AUDIT_REPORT.md
DIL_SERVICES = [
    "products",
    "evidence", 
    "competitive-intel",
    "roi",
    "enrichment",
    "value-hypotheses",
    "narratives",
    "intelligence"
]

def extract_openapi_endpoints() -> Dict[str, List[str]]:
    """Extract all endpoints from OpenAPI specs"""
    endpoints = {}
    
    for spec_file in CONTRACTS_DIR.glob("*.json"):
        layer = spec_file.stem.replace("layer", "").replace("-", "")
        try:
            with open(spec_file, 'r') as f:
                spec = json.load(f)
            
            paths = spec.get("paths", {})
            layer_endpoints = []
            
            for path, methods in paths.items():
                for method in methods.keys():
                    endpoint = f"{method.upper()} {path}"
                    layer_endpoints.append(endpoint)
            
            endpoints[layer] = layer_endpoints
        except Exception as e:
            print(f"Error reading {spec_file}: {e}")
    
    return endpoints

def extract_dil_hooks() -> Dict[str, List[str]]:
    """Extract all DIL hooks from the codebase"""
    hooks = {}
    
    for service in DIL_SERVICES:
        service_hooks = []
        
        # Look for hook files matching the service
        hook_patterns = [
            f"use{service.capitalize()}",
            f"use{service.replace('-', '')}",
            service
        ]
        
        for hook_file in HOOKS_DIR.glob("use*.ts*"):
            hook_name = hook_file.stem
            
            # Check if hook matches service
            for pattern in hook_patterns:
                if pattern.lower() in hook_name.lower():
                    service_hooks.append(hook_name)
                    break
        
        hooks[service] = service_hooks
    
    return hooks

def analyze_coverage(openapi_endpoints: Dict[str, List[str]], dil_hooks: Dict[str, List[str]]) -> Dict:
    """Analyze coverage between OpenAPI endpoints and DIL hooks"""
    
    total_openapi_endpoints = sum(len(endpoints) for endpoints in openapi_endpoints.values())
    total_dil_hooks = sum(len(hooks) for hooks in dil_hooks.values())
    
    services_with_hooks = [s for s, hooks in dil_hooks.items() if hooks]
    services_without_hooks = [s for s, hooks in dil_hooks.items() if not hooks]
    
    return {
        "total_openapi_endpoints": total_openapi_endpoints,
        "total_dil_hooks": total_dil_hooks,
        "services_with_hooks": services_with_hooks,
        "services_without_hooks": services_without_hooks,
        "coverage_percentage": round((len(services_with_hooks) / len(DIL_SERVICES)) * 100, 1) if DIL_SERVICES else 0
    }

def main():
    print("=" * 80)
    print("OpenAPI ↔ DIL Hook Coverage Analysis")
    print("=" * 80)
    print()
    
    # Extract data
    openapi_endpoints = extract_openapi_endpoints()
    dil_hooks = extract_dil_hooks()
    
    # Analyze
    analysis = analyze_coverage(openapi_endpoints, dil_hooks)
    
    # Print results
    print("OpenAPI Endpoints by Layer:")
    print("-" * 80)
    for layer, endpoints in openapi_endpoints.items():
        print(f"  {layer}: {len(endpoints)} endpoints")
    print(f"  Total: {analysis['total_openapi_endpoints']} endpoints")
    print()
    
    print("DIL Hooks by Service:")
    print("-" * 80)
    for service, hooks in dil_hooks.items():
        status = "✓" if hooks else "✗"
        print(f"  {status} {service}: {len(hooks)} hooks")
        if hooks:
            for hook in hooks:
                print(f"      - {hook}")
    print(f"  Total: {analysis['total_dil_hooks']} hooks")
    print()
    
    print("Coverage Summary:")
    print("-" * 80)
    print(f"  Services with hooks: {len(analysis['services_with_hooks'])}/{len(DIL_SERVICES)}")
    print(f"  Services without hooks: {len(analysis['services_without_hooks'])}")
    print(f"  Coverage: {analysis['coverage_percentage']}%")
    print()
    
    if analysis['services_without_hooks']:
        print("Missing DIL Hooks:")
        print("-" * 80)
        for service in analysis['services_without_hooks']:
            print(f"  - {service}")
        print()
    
    print("=" * 80)
    print("Analysis Complete")
    print("=" * 80)

if __name__ == "__main__":
    main()
