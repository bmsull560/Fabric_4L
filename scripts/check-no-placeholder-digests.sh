#!/usr/bin/env bash
# check-no-placeholder-digests.sh
#
# Exits 1 if any sequential placeholder digest (sha256:1111...1111 through
# sha256:ffff...ffff) is found in the given file(s).
#
# Usage:
#   bash scripts/check-no-placeholder-digests.sh k8s/envs/prod/kustomization.yaml
#   bash scripts/check-no-placeholder-digests.sh k8s/envs/prod/*.yaml
#
# Intended for pre-commit hooks and manual verification.
# CI enforcement is in .github/workflows/environment-promotion.yml.
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <file> [file ...]" >&2
  exit 1
fi

FOUND=0

for FILE in "$@"; do
  if [[ ! -f "$FILE" ]]; then
    echo "ERROR: file not found: $FILE" >&2
    exit 1
  fi

  # Pattern: sha256: followed by 64 identical hex characters (e.g. 1111...1111).
  # Uses grep -P (PCRE) for backreference; falls back to a digit-by-digit check.
  if grep -Eq 'sha256:([0-9a-f])\1{63}' "$FILE" 2>/dev/null; then
    echo "ERROR: placeholder digest(s) found in $FILE:" >&2
    grep -E 'sha256:([0-9a-f])\1{63}' "$FILE" | sed 's/^/  /' >&2
    FOUND=1
  fi
done

if [[ $FOUND -ne 0 ]]; then
  echo "" >&2
  echo "Run scripts/ci/prepare_kustomize_deploy.sh to resolve real digests before deploying." >&2
  exit 1
fi

echo "No placeholder digests found."
