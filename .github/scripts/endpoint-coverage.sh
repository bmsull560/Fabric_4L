#!/usr/bin/env bash
# CI Gate: endpoint-coverage
# Counts how many DIL hook families are imported by at least one page file.
# Reports coverage percentage. Exits non-zero if coverage drops below threshold.
#
# Usage: bash .github/scripts/endpoint-coverage.sh [min_coverage_pct]

set -euo pipefail

MIN_COVERAGE=${1:-80}
HOOKS_DIR="apps/web/src/hooks"
PAGES_DIR="apps/web/src/pages"
EXIT_CODE=0

# Discover all hook families (files matching use*.ts)
HOOK_FILES=$(find "$HOOKS_DIR" -maxdepth 1 -name "use*.ts" -not -name "*.test.*" -not -name "*.spec.*" | sort)
TOTAL_FAMILIES=0
WIRED_FAMILIES=0
UNWIRED=()

echo "📊 Endpoint Coverage Report"
echo "═══════════════════════════════════════════════════"
echo ""

for hook_file in $HOOK_FILES; do
  family=$(basename "$hook_file" .ts)
  TOTAL_FAMILIES=$((TOTAL_FAMILIES + 1))

  # Check if any page file imports from this hook family
  import_count=$(grep -rl "from.*hooks/$family\|from.*hooks.*$family" "$PAGES_DIR" 2>/dev/null | grep -v "_deprecated" | wc -l || true)

  if [ "$import_count" -gt 0 ]; then
    WIRED_FAMILIES=$((WIRED_FAMILIES + 1))
    echo "  ✅ $family — imported by $import_count page(s)"
  else
    # Also check barrel imports
    barrel_count=$(grep -rl "from.*@/hooks" "$PAGES_DIR" 2>/dev/null | xargs grep -l "$family\|$(echo "$family" | sed 's/^use/use/')" 2>/dev/null | grep -v "_deprecated" | wc -l || true)
    if [ "$barrel_count" -gt 0 ]; then
      WIRED_FAMILIES=$((WIRED_FAMILIES + 1))
      echo "  ✅ $family — imported via barrel by $barrel_count page(s)"
    else
      UNWIRED+=("$family")
      echo "  ⚠️  $family — NOT imported by any page"
    fi
  fi
done

echo ""
echo "═══════════════════════════════════════════════════"

if [ "$TOTAL_FAMILIES" -gt 0 ]; then
  COVERAGE=$((WIRED_FAMILIES * 100 / TOTAL_FAMILIES))
else
  COVERAGE=100
fi

echo "Coverage: $WIRED_FAMILIES / $TOTAL_FAMILIES families ($COVERAGE%)"
echo "Threshold: ${MIN_COVERAGE}%"
echo ""

if [ "$COVERAGE" -lt "$MIN_COVERAGE" ]; then
  echo "❌ Coverage ($COVERAGE%) is below threshold ($MIN_COVERAGE%)"
  if [ ${#UNWIRED[@]} -gt 0 ]; then
    echo ""
    echo "Unwired hook families:"
    for u in "${UNWIRED[@]}"; do
      echo "  - $u"
    done
  fi
  EXIT_CODE=1
else
  echo "✅ Coverage meets threshold."
fi

exit $EXIT_CODE
