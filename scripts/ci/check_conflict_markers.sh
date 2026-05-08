#!/usr/bin/env bash
set -euo pipefail

# Scan tracked source files for unresolved merge conflict markers.
# Restricting to source-like files avoids expected marker-like strings in lockfiles or binaries.
# Pattern requires git conflict markers: <<<<<<< HEAD, =======, >>>>>>> branch-name

PATTERN='^(<<<<<<< .+|=======\s*$|>>>>>>> .+)$'

mapfile -t files < <(git ls-files \
  '*.py' '*.pyi' '*.sh' '*.bash' '*.zsh' \
  '*.js' '*.jsx' '*.ts' '*.tsx' '*.mjs' '*.cjs' \
  '*.json' '*.jsonc' '*.yaml' '*.yml' '*.toml' '*.ini' '*.cfg' \
  '*.md' '*.sql' '*.tf' '*.hcl' '*.dockerfile' 'Dockerfile*' \
  'Makefile' '*.mk')

if [ ${#files[@]} -eq 0 ]; then
  echo 'No tracked source files found to scan.'
  exit 0
fi

set +e
matches=$(git grep -nE "$PATTERN" -- "${files[@]}")
status=$?
set -e

if [ "$status" -eq 0 ]; then
  echo '❌ Unresolved merge conflict markers found:'
  echo "$matches"
  exit 1
fi

if [ "$status" -eq 1 ]; then
  echo '✅ No unresolved merge conflict markers found in tracked source files.'
  exit 0
fi

echo '❌ Conflict marker scan failed unexpectedly.'
exit "$status"
