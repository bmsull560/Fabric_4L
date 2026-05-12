#!/usr/bin/env bash
set -euo pipefail

# Scan all tracked files for unresolved git merge conflict markers.
PATTERN='^(<<<<<<< .+|=======\s*$|>>>>>>> .+)$'

set +e
matches=$(git grep -nI -E "$PATTERN" -- .)
status=$?
set -e

if [ "$status" -eq 0 ]; then
  echo '❌ Unresolved merge conflict markers found:'
  echo "$matches"
  exit 1
fi

if [ "$status" -eq 1 ]; then
  echo '✅ No unresolved merge conflict markers found in tracked files.'
  exit 0
fi

echo '❌ Conflict marker scan failed unexpectedly.'
exit "$status"
