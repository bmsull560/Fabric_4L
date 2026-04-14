#!/usr/bin/env bash
set -euo pipefail

MATRIX_FILE="docs/compliance/control-matrix.md"

if [[ ! -f "$MATRIX_FILE" ]]; then
  echo "::error title=Missing control matrix::$MATRIX_FILE is required"
  exit 1
fi

# Determine diff base.
BASE_REF="${GITHUB_BASE_REF:-main}"

if git rev-parse --verify "origin/${BASE_REF}" >/dev/null 2>&1; then
  BASE_COMMIT="origin/${BASE_REF}"
else
  BASE_COMMIT="HEAD~1"
fi

CHANGED_TRACKED="$(git diff --name-only "${BASE_COMMIT}" || true)"
CHANGED_UNTRACKED="$(git ls-files --others --exclude-standard || true)"
CHANGED_FILES="$(printf '%s\n%s\n' "${CHANGED_TRACKED}" "${CHANGED_UNTRACKED}" | awk 'NF' | sort -u)"

if [[ -z "$CHANGED_FILES" ]]; then
  echo "No changed files detected; skipping control matrix policy check."
  exit 0
fi

# Paths considered security/governance-impacting.
NEEDS_MATRIX_REGEX='^(value-fabric/shared/identity/|value-fabric/shared/audit/|value-fabric/layer[0-9]+-.*/migrations/|contracts/tool-manifests/|k8s/|monitoring/|docs/secrets-management\.md|docs/SECRETS\.md|docs/runbooks/|\.github/workflows/security-gates\.yml|\.github/workflows/pr-checks\.yml)'

if ! printf '%s\n' "$CHANGED_FILES" | rg -q "$NEEDS_MATRIX_REGEX"; then
  echo "No security/governance-sensitive files changed; matrix update not required."
  exit 0
fi

if printf '%s\n' "$CHANGED_FILES" | rg -qx "$MATRIX_FILE"; then
  echo "Control matrix updated in this PR."
  exit 0
fi

echo "::error title=Control matrix update required::Security/governance-sensitive files changed, but ${MATRIX_FILE} was not updated."
echo "Changed files requiring matrix review:"
printf '%s\n' "$CHANGED_FILES" | rg "$NEEDS_MATRIX_REGEX" || true
exit 1
