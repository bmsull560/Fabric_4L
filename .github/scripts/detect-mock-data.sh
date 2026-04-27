#!/usr/bin/env bash
# CI Gate: detect-mock-data
# Scans frontend page files for hardcoded mock data arrays that should be
# replaced by real API hook calls. Exits non-zero if any are found.
#
# Usage: bash .github/scripts/detect-mock-data.sh

set -euo pipefail

PAGES_DIR="frontend/client/src/pages"
EXIT_CODE=0
FINDINGS=()

# Patterns that indicate hardcoded mock data
MOCK_PATTERNS=(
  'MOCK_'
  'const mock'
  'const MOCK'
  'const fake'
  'const FAKE'
  'const stub'
  'const STUB'
  'mockData'
  'sampleData'
  'dummyData'
  'placeholderData.*=.*\['
)

echo "🔍 Scanning $PAGES_DIR for hardcoded mock data..."
echo ""

for pattern in "${MOCK_PATTERNS[@]}"; do
  while IFS= read -r match; do
    if [ -n "$match" ]; then
      # Skip _deprecated directory
      if echo "$match" | grep -q "_deprecated"; then
        continue
      fi
      # Skip test files
      if echo "$match" | grep -q "\.test\.\|\.spec\."; then
        continue
      fi
      FINDINGS+=("$match")
    fi
  done < <(grep -rn "$pattern" "$PAGES_DIR" 2>/dev/null || true)
done

if [ ${#FINDINGS[@]} -gt 0 ]; then
  echo "❌ Found ${#FINDINGS[@]} mock data pattern(s) in page files:"
  echo ""
  for finding in "${FINDINGS[@]}"; do
    echo "  $finding"
  done
  echo ""
  echo "These should be replaced with real API hook calls."
  EXIT_CODE=1
else
  echo "✅ No hardcoded mock data found in page files."
fi

exit $EXIT_CODE
