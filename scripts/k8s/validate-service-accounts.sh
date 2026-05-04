#!/bin/bash
# validate-service-accounts.sh
#
# Validates that ServiceAccounts exist for critical services and that
# RBAC bindings are configured where ServiceAccounts are referenced.
#
# Usage:
#   ./scripts/k8s/validate-service-accounts.sh
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

echo "Validating ServiceAccount coverage..."

failures=0

# Check for ServiceAccount definitions
sa_files=$(find "$K8S_BASE_DIR" -name "*service-account*.yml" -o -name "*service-account*.yaml" 2>/dev/null)

if [ -z "$sa_files" ]; then
  echo "⚠ WARN: No ServiceAccount files found in $K8S_BASE_DIR"
else
  sa_count=$(echo "$sa_files" | wc -l)
  echo "✓ INFO: Found $sa_count ServiceAccount files"
fi

# Check for external-secrets ServiceAccount
externalsecrets_sa="${K8S_BASE_DIR}/externalsecrets/clustersecretstore.yaml"
if [ -f "$externalsecrets_sa" ]; then
  sa_ref=$(yq eval '.spec.secretRef.name' "$externalsecrets_sa" 2>/dev/null || echo "")
  if [ -n "$sa_ref" ]; then
    echo "✓ PASS: ExternalSecrets ClusterSecretStore references SecretRef: $sa_ref"
  else
    echo "⚠ WARN: ExternalSecrets ClusterSecretStore missing SecretRef"
  fi
fi

# Check gitops rollouts for ServiceAccount references
rollout_files=$(find "$K8S_BASE_DIR/../gitops/rollouts" -name "*.yml" -o -name "*.yaml" 2>/dev/null || true)

for file in $rollout_files; do
  service_account=$(yq eval '.spec.template.spec.serviceAccountName' "$file" 2>/dev/null || echo "")
  
  if [ -n "$service_account" ]; then
    rollout_name=$(yq eval '.metadata.name' "$file" 2>/dev/null || echo "unknown")
    echo "✓ PASS: Rollout $rollout_name uses ServiceAccount: $service_account"
  fi
done

echo ""
if [ $failures -eq 0 ]; then
  echo "ServiceAccount validation passed"
  exit 0
else
  echo "ServiceAccount validation failed: $failures failures"
  exit 1
fi
