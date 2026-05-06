#!/usr/bin/env bash
set -euo pipefail

status=0
for policy in k8s/vault/policies/*.hcl; do
  name="$(basename "$policy")"

  # Only break-glass policy may use wide secret wildcard paths.
  if [[ "$name" != *"break-glass"* ]]; then
    if grep -Eq 'path[[:space:]]+"secret/\*"' "$policy"; then
      echo "ERROR: wildcard secret path is forbidden in non-break-glass policy: $policy"
      status=1
    fi
  fi
done

exit "$status"
