#!/bin/bash
# validate-non-root-posture.sh
#
# Validates that all Deployments, StatefulSets, and DaemonSets in the
# k8s/base directory have securityContext.runAsNonRoot=true set.
#
# Usage:
#   ./scripts/k8s/validate-non-root-posture.sh
#
# Returns:
#   0 if all resources have non-root posture
#   1 if validation fails

set -euo pipefail

# Check if yq is installed
if ! command -v yq &> /dev/null; then
  echo "✗ FAIL: yq is not installed. Install with: brew install yq (macOS) or snap install yq (Linux)"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_BASE_DIR="${SCRIPT_DIR}/../../k8s/base"

echo "Validating non-root posture across all resources..."

# Find all yaml files in k8s/base
yaml_files=$(find "$K8S_BASE_DIR" -name "*.yml" -o -name "*.yaml")

if [ -z "$yaml_files" ]; then
  echo "No YAML files found in $K8S_BASE_DIR"
  exit 1
fi

# Track failures
failures=0
total=0

for file in $yaml_files; do
  # Check for Deployment, StatefulSet, or DaemonSet
  kind=$(yq eval '.kind' "$file" 2>/dev/null || echo "")
  
  if [[ "$kind" =~ ^(Deployment|StatefulSet|DaemonSet)$ ]]; then
    total=$((total + 1))
    
    # Check for runAsNonRoot in pod securityContext
    pod_non_root=$(yq eval '.spec.template.spec.securityContext.runAsNonRoot' "$file" 2>/dev/null || echo "null")
    
    # Check for runAsNonRoot in container securityContext
    container_non_root=$(yq eval '.spec.template.spec.containers[].securityContext.runAsNonRoot' "$file" 2>/dev/null || echo "null")
    
    # Check initContainers if they exist and validate their securityContext
    init_container_non_root=$(yq eval '.spec.template.spec.initContainers[].securityContext.runAsNonRoot' "$file" 2>/dev/null || echo "null")
    
    # If initContainers exist, they should also have non-root posture
    if [ "$init_container_non_root" != "null" ] && [ "$init_container_non_root" != "true" ]; then
      echo "✗ FAIL: $file ($kind $resource_name) - initContainers missing runAsNonRoot"
      failures=$((failures + 1))
    fi
    
    resource_name=$(yq eval '.metadata.name' "$file" 2>/dev/null || echo "unknown")
    
    if [ "$pod_non_root" != "true" ] && [ "$container_non_root" != "true" ]; then
      echo "✗ FAIL: $file ($kind $resource_name) - runAsNonRoot not set in pod or container securityContext"
      failures=$((failures + 1))
    else
      echo "✓ PASS: $file ($kind $resource_name) - runAsNonRoot set"
    fi
  fi
done

echo ""
echo "Validation complete: $failures failures out of $total resources checked"

if [ $failures -eq 0 ]; then
  echo "All resources have non-root posture configured"
  exit 0
else
  echo "Validation failed: $failures resources missing non-root posture"
  exit 1
fi
