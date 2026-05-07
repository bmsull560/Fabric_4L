#!/usr/bin/env python3
"""Production auth bypass prevention gate.

Scans production-like deployment manifests and compose files
for insecure authentication bypass flags and hardcoded weak secrets.
"""

import os
import sys
import glob
from pathlib import Path

# Files to check
PROD_FILES = [
    "docker-compose.live.yml",
    "docker-compose.full.yml",
]

# Add any k8s prod/staging overlays if they exist
for root, _, _ in os.walk("k8s/envs/prod"):
    PROD_FILES.extend(glob.glob(os.path.join(root, "*.yml")))
    PROD_FILES.extend(glob.glob(os.path.join(root, "*.yaml")))

for root, _, _ in os.walk("k8s/envs/staging"):
    PROD_FILES.extend(glob.glob(os.path.join(root, "*.yml")))
    PROD_FILES.extend(glob.glob(os.path.join(root, "*.yaml")))

BANNED_PATTERNS = [
    "DEV_AUTH_BYPASS",
    "ALLOW_INSECURE_DEV_AUTH_BYPASS",
    "VITE_ENABLE_MOCK_FALLBACK: \"true\"",
    "VITE_ENABLE_MOCK_FALLBACK: true",
    "dev-local-secret-do-not-use-in-production",
    "dev-local-service-auth-secret",
]

def main():
    has_errors = False
    
    for filepath in PROD_FILES:
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for idx, line in enumerate(content.splitlines(), 1):
            for pattern in BANNED_PATTERNS:
                if pattern in line:
                    print(f"ERROR: Insecure pattern '{pattern}' found in {filepath}:{idx}")
                    has_errors = True
                    
    if has_errors:
        print("\nProduction auth bypass check failed.")
        print("Please remove all DEV_AUTH_BYPASS flags, mock fallbacks, and weak secrets from production configs.")
        sys.exit(1)
        
    print("Production auth bypass check passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
