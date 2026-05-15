#!/usr/bin/env bash
# Resolve the Kubernetes namespace for a given environment by reading the
# namespace field from the canonical kustomize overlay. Prints the namespace
# to stdout. Exits non-zero if the environment is unknown or the overlay file
# is missing or has no namespace field.
#
# Usage: resolve-namespace.sh <environment>
#   environment: production | staging | dev

set -euo pipefail

ENVIRONMENT="${1:-}"

case "$ENVIRONMENT" in
  production) OVERLAY_FILE="k8s/overlays/production/kustomization.yaml" ;;
  staging)    OVERLAY_FILE="k8s/overlays/staging/kustomization.yaml" ;;
  dev)        OVERLAY_FILE="k8s/envs/dev/kustomization.yaml" ;;
  *)
    echo "Error: unknown environment '${ENVIRONMENT}'. Must be one of: production, staging, dev" >&2
    exit 1 ;;
esac

if [[ ! -f "$OVERLAY_FILE" ]]; then
  echo "Error: overlay file not found: $OVERLAY_FILE" >&2
  exit 1
fi

NAMESPACE=$(grep -E '^namespace:' "$OVERLAY_FILE" | awk '{print $2}' | tr -d '"' | head -1)

if [[ -z "$NAMESPACE" ]]; then
  echo "Error: no 'namespace:' field found in $OVERLAY_FILE" >&2
  exit 1
fi

echo "$NAMESPACE"
