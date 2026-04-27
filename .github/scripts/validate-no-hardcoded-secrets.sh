#!/usr/bin/env bash
# validate-no-hardcoded-secrets.sh
# Prevents hardcoded secrets from being committed to .env.production and .env.staging.
#
# Checks:
#   1. REGISTRY_TOKEN must not have a non-empty value
#   2. Known secret patterns (API keys, tokens) must not appear
#
# Exit codes:
#   0 — No violations found
#   1 — One or more hardcoded secrets detected
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
EXIT_CODE=0

# Files to scan (production and staging only — dev/test are acceptable)
ENV_FILES=(
  "frontend/.env.production"
  "frontend/.env.staging"
)

# Secret key names that must not have hardcoded values
SECRET_KEYS=(
  "REGISTRY_TOKEN"
  "VITE_API_SECRET"
  "JWT_SECRET"
  "DATABASE_PASSWORD"
  "REDIS_PASSWORD"
  "NEO4J_PASSWORD"
)

# Known secret patterns (prefix-based detection)
SECRET_PATTERNS=(
  "suk-"       # shadcnuikit registry tokens
  "sk-"        # OpenAI-style API keys
  "ghp_"       # GitHub personal access tokens
  "ghs_"       # GitHub server tokens
  "glpat-"     # GitLab tokens
)

echo "================================================================"
echo "Hardcoded Secret Detection — .env.production / .env.staging"
echo "================================================================"
echo

for env_file in "${ENV_FILES[@]}"; do
  full_path="${REPO_ROOT}/${env_file}"
  if [[ ! -f "$full_path" ]]; then
    echo "  SKIP: ${env_file} (file not found)"
    continue
  fi

  echo "  Scanning: ${env_file}"

  while IFS= read -r line; do
    # Skip comments and blank lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// /}" ]] && continue

    # Extract key=value
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.+)$ ]]; then
      key="${BASH_REMATCH[1]}"
      value="${BASH_REMATCH[2]}"

      # Check secret key names
      for secret_key in "${SECRET_KEYS[@]}"; do
        if [[ "$key" == "$secret_key" && -n "$value" ]]; then
          echo "    ERROR: ${env_file}: ${key} has a hardcoded value"
          EXIT_CODE=1
        fi
      done

      # Check secret patterns in any value
      for pattern in "${SECRET_PATTERNS[@]}"; do
        if [[ "$value" == ${pattern}* ]]; then
          echo "    ERROR: ${env_file}: ${key} value matches secret pattern '${pattern}*'"
          EXIT_CODE=1
        fi
      done
    fi
  done < "$full_path"
done

echo
echo "================================================================"
if [[ $EXIT_CODE -eq 0 ]]; then
  echo "PASS: No hardcoded secrets detected"
else
  echo "FAIL: Hardcoded secrets found in committed .env files"
  echo
  echo "To fix:"
  echo "  1. Remove the secret value from the .env file"
  echo "  2. Add a comment: # Set via CI secrets or runtime injection"
  echo "  3. Inject the value at deploy time from your secrets manager"
fi
echo "================================================================"

exit $EXIT_CODE
