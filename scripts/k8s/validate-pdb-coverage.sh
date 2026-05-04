#!/bin/bash
# validate-pdb-coverage.sh
#
# Validates that PodDisruptionBudgets exist for all critical services
# (frontend, layer1-ingestion, layer2-extraction, layer3-knowledge, layer4-agents, layer5-ground-truth, layer6-benchmarks)
#
# Usage:
#   ./scripts/k8s/validate-pdb-coverage.sh
#
# Returns:
#   0 if all critical services have PDBs
#   1 if validation fails

set -euo pipefail

# Check if yq is installed
if ! command -v yq &> /dev/null; then
  echo "✗ FAIL: yq is not installed. Install with: brew install yq (macOS) or snap install yq (Linux)"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_BASE_DIR="${SCRIPT_DIR}/../../k8s/base"

echo "Validating PodDisruptionBudget coverage..."

failures=0

# Critical services that should have PDBs
critical_services=(
  "frontend"
  "layer1-ingestion"
  "layer2-extraction"
  "layer3-knowledge"
  "layer4-agents"
  "layer5-ground-truth"
  "layer6-benchmarks"
)

pdb_dir="${K8S_BASE_DIR}/pdb"
if [ ! -d "$pdb_dir" ]; then
  echo "✗ FAIL: PDB directory not found at $pdb_dir"
  exit 1
fi

for service in "${critical_services[@]}"; do
  # Look for PDB file matching the service
  pdb_file=$(find "$pdb_dir" -name "${service}*.yml" -o -name "${service}*.yaml" 2>/dev/null | head -1)
  
  if [ -n "$pdb_file" ]; then
    # Check that PDB has minAvailable or maxUnavailable set
    min_available=$(yq eval '.spec.minAvailable' "$pdb_file" 2>/dev/null || echo "null")
    max_unavailable=$(yq eval '.spec.maxUnavailable' "$pdb_file" 2>/dev/null || echo "null")
    
    if [ "$min_available" != "null" ] || [ "$max_unavailable" != "null" ]; then
      echo "✓ PASS: $service has PDB with availability policy"
    else
      echo "✗ FAIL: $service PDB exists but has no minAvailable or maxUnavailable"
      failures=$((failures + 1))
    fi
  else
    echo "✗ FAIL: $service missing PodDisruptionBudget"
    failures=$((failures + 1))
  fi
done

echo ""
if [ $failures -eq 0 ]; then
  echo "PodDisruptionBudget coverage validation passed"
  exit 0
else
  echo "PodDisruptionBudget coverage validation failed: $failures failures"
  exit 1
fi
