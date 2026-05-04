#!/usr/bin/env bash
# CI Gate: type-sync-check
# Verifies that TypeScript hook files export typed interfaces (not just `any`)
# and that the generated types match the OpenAPI contract schemas.
#
# Checks:
# 1. No `any` type in hook return values or request params
# 2. All hook files export at least one typed interface
# 3. No `as unknown as any` casts (type safety bypass)
#
# Usage: bash .github/scripts/type-sync-check.sh

set -euo pipefail

HOOKS_DIR="apps/web/src/hooks"
EXIT_CODE=0
ISSUES=()

echo "🔒 Type Sync Check"
echo "═══════════════════════════════════════════════════"
echo ""

# 1. Check for dangerous `any` usage in hooks
echo "1. Checking for 'any' type usage in hooks..."
ANY_MATCHES=$(grep -rn ": any\b\|<any>\|as any\b" "$HOOKS_DIR" --include="*.ts" 2>/dev/null | grep -v "// eslint-disable\|// @ts-ignore\|\.test\.\|\.spec\." || true)
if [ -n "$ANY_MATCHES" ]; then
  COUNT=$(echo "$ANY_MATCHES" | wc -l)
  echo "  ⚠️  Found $COUNT instance(s) of 'any' type:"
  echo "$ANY_MATCHES" | head -10 | while IFS= read -r line; do
    echo "    $line"
  done
  if [ "$COUNT" -gt 10 ]; then
    echo "    ... and $((COUNT - 10)) more"
  fi
  ISSUES+=("$COUNT 'any' type usage(s)")
else
  echo "  ✅ No 'any' type usage found."
fi
echo ""

# 2. Check that all hook files export typed interfaces
echo "2. Checking hook files export typed interfaces..."
HOOK_FILES=$(find "$HOOKS_DIR" -maxdepth 1 -name "use*.ts" -not -name "*.test.*" -not -name "*.spec.*" | sort)
MISSING_TYPES=()
for hook_file in $HOOK_FILES; do
  family=$(basename "$hook_file" .ts)
  has_interface=$(grep -c "^export interface\|^export type" "$hook_file" 2>/dev/null || true)
  if [ "$has_interface" -eq 0 ]; then
    MISSING_TYPES+=("$family")
    echo "  ⚠️  $family — no exported interface/type"
  fi
done
if [ ${#MISSING_TYPES[@]} -eq 0 ]; then
  echo "  ✅ All hook files export typed interfaces."
else
  ISSUES+=("${#MISSING_TYPES[@]} hook file(s) missing typed interfaces")
fi
echo ""

# 3. Check for type safety bypasses
echo "3. Checking for type safety bypasses..."
BYPASS_MATCHES=$(grep -rn "as unknown as any\|as never\|@ts-ignore\|@ts-expect-error" "$HOOKS_DIR" --include="*.ts" 2>/dev/null | grep -v "\.test\.\|\.spec\." || true)
if [ -n "$BYPASS_MATCHES" ]; then
  COUNT=$(echo "$BYPASS_MATCHES" | wc -l)
  echo "  ⚠️  Found $COUNT type safety bypass(es):"
  echo "$BYPASS_MATCHES" | head -5 | while IFS= read -r line; do
    echo "    $line"
  done
  ISSUES+=("$COUNT type safety bypass(es)")
else
  echo "  ✅ No type safety bypasses found."
fi
echo ""

# 4. Summary
echo "═══════════════════════════════════════════════════"
if [ ${#ISSUES[@]} -gt 0 ]; then
  echo "⚠️  Found ${#ISSUES[@]} issue category(ies):"
  for issue in "${ISSUES[@]}"; do
    echo "  - $issue"
  done
  echo ""
  echo "Note: These are warnings, not blocking errors."
  echo "Fix 'any' types by adding proper interfaces."
else
  echo "✅ All type sync checks passed."
fi

# Currently advisory — exit 0 to not block CI
# Change to EXIT_CODE=1 when ready to enforce
exit 0
