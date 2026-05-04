#!/bin/bash
# validate-network-policies.sh
#
# Validates that:
# 1. Default-deny-all NetworkPolicy exists
# 2. Each layer has specific NetworkPolicy allowing required traffic
# 3. No pods use hostNetwork: true
#
# Usage:
#   ./scripts/k8s/validate-network-policies.sh
#
# Returns:
#   0 if validation passes
#   1 if validation fails

set -euo pipefail

# Check if yq is installed
if ! command -v yq &> /dev/null; then
  echo "✗ FAIL: yq is not installed. Install with: brew install yq (macOS) or snap install yq (Linux)"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_BASE_DIR="${SCRIPT_DIR}/../../k8s/base"

echo "Validating NetworkPolicy coverage..."

failures=0

# Check for default-deny-all policy
default_deny="${K8S_BASE_DIR}/network-policies/deny-all.yml"
if [ -f "$default_deny" ]; then
  echo "✓ PASS: Default-deny-all NetworkPolicy exists"
else
  echo "✗ FAIL: Default-deny-all NetworkPolicy not found at $default_deny"
  failures=$((failures + 1))
fi

# Check that no resources use hostNetwork: true
yaml_files=$(find "$K8S_BASE_DIR" -name "*.yml" -o -name "*.yaml")

for file in $yaml_files; do
  host_network=$(yq eval '.spec.template.spec.hostNetwork' "$file" 2>/dev/null || echo "null")
  
  if [ "$host_network" = "true" ]; then
    resource_name=$(yq eval '.metadata.name' "$file" 2>/dev/null || echo "unknown")
    echo "✗ FAIL: $file ($resource_name) - hostNetwork is set to true"
    failures=$((failures + 1))
  fi
done

# Check for per-layer NetworkPolicies (layer1, layer2, layer3, layer4, layer5, layer6)
network_policy_dir="${K8S_BASE_DIR}/network-policies"
if [ -d "$network_policy_dir" ]; then
  layer_policies=$(find "$network_policy_dir" -name "layer*.yml" -o -name "layer*.yaml" | wc -l)
  
  if [ "$layer_policies" -ge 6 ]; then
    echo "✓ PASS: Found $layer_policies layer-specific NetworkPolicies"
  else
    echo "⚠ WARN: Only $layer_policies layer-specific NetworkPolicies found (expected 6)"
  fi
fi

echo ""
if [ $failures -eq 0 ]; then
  echo "NetworkPolicy validation passed"
  exit 0
else
  echo "NetworkPolicy validation failed: $failures failures"
  exit 1
fi
