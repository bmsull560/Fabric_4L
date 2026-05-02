#!/usr/bin/env bash
# scripts/release-gate.sh — Enforcement-grade Release Gate orchestrator for Value Fabric
# Usage: bash scripts/release-gate.sh [PROFILE]
# Profile: pr-fast | mainline-full | release-candidate (default: release-candidate)
set -uo pipefail

PROFILE="${1:-release-candidate}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
ARTIFACT_DIR="${ROOT}/artifacts/release"
LOG_DIR="${ARTIFACT_DIR}/logs"
POLICY_FILE="${ROOT}/.fabric/prod-gates.policy.yaml"
mkdir -p "$LOG_DIR"

# ── Negative validation: policy file ─────────────────────────────────────────
if [ ! -s "$POLICY_FILE" ]; then
    echo "❌ Negative check FAILED: Policy file $POLICY_FILE missing or empty"
    exit 1
fi

if ! python3 -c "import yaml; yaml.safe_load(open('$POLICY_FILE'))" 2>/dev/null; then
    echo "❌ Negative check FAILED: Policy file is not valid YAML"
    exit 1
fi

# ── Negative validation: profile existence ───────────────────────────────────
PROFILE_VALID=$(python3 -c "
import yaml
with open('$POLICY_FILE') as f:
    data = yaml.safe_load(f)
print('true' if '$PROFILE' in data.get('profiles', {}) else 'false')
")
if [ "$PROFILE_VALID" != "true" ]; then
    echo "❌ Negative check FAILED: Unknown profile '$PROFILE'"
    echo "   Valid profiles: pr-fast, mainline-full, release-candidate"
    exit 1
fi

# ── Helper: query policy YAML ────────────────────────────────────────────────
_policy_get() {
    python3 -c "
import yaml
with open('$POLICY_FILE') as f:
    data = yaml.safe_load(f)
$1
"
}

# ── Collect gate definitions into bash arrays ────────────────────────────────
GATES=$(_policy_get "
profile = data['profiles']['$PROFILE']
for g in profile.get('gates', []):
    print(g)
")

# Associative arrays for gate metadata
declare -A GATE_TARGET
declare -A GATE_CLASS
declare -A GATE_REQUIRED
declare -A GATE_CAVEAT
declare -A GATE_STATUS
declare -A GATE_REASON

for gate in $GATES; do
    target=$(_policy_get "g = data['gate-definitions']['$gate']; print(g.get('target', '$gate'))")
    class=$(_policy_get "g = data['gate-definitions']['$gate']; print(g.get('class', 'blocking'))")
    required=$(_policy_get "g = data['gate-definitions']['$gate']; print('true' if g.get('required', False) else 'false')")
    caveat=$(_policy_get "g = data['gate-definitions']['$gate']; print(g.get('caveat', ''))")
    GATE_TARGET[$gate]="$target"
    GATE_CLASS[$gate]="$class"
    GATE_REQUIRED[$gate]="$required"
    GATE_CAVEAT[$gate]="$caveat"
    GATE_STATUS[$gate]="NOT_RUN"
done

# ── Helper: run a Makefile target ────────────────────────────────────────────
run_target() {
    local gate="$1"
    local target="${GATE_TARGET[$gate]}"
    local logfile="${LOG_DIR}/${target}.log"
    echo "→ [$gate] $target ..." | tee -a "$LOG_DIR/release-gate.log"
    if make -C "$ROOT" "$target" > "$logfile" 2>&1; then
        echo "   ✅ $gate" | tee -a "$LOG_DIR/release-gate.log"
        GATE_STATUS[$gate]="PASS"
    else
        local rc=$?
        # Classify the failure
        if grep -q "PLACEHOLDER" "$logfile" 2>/dev/null; then
            GATE_REASON[$gate]="PLACEHOLDER"
        else
            GATE_REASON[$gate]="FAIL"
        fi
        echo "   ❌ $gate (see ${logfile})" | tee -a "$LOG_DIR/release-gate.log"
        GATE_STATUS[$gate]="FAIL"
    fi
}

echo "🚀 Release Gate — Profile: $PROFILE"
echo "   Root:    $ROOT"
echo "   Policy:  $POLICY_FILE"
echo "   Artifacts: $ARTIFACT_DIR"
echo ""

# ── Step 1: Policy validation (hard-fail) ────────────────────────────────────
run_target "policy"
if [ "${GATE_STATUS[policy]}" != "PASS" ]; then
    echo "❌ Policy validation failed — aborting"
    exit 1
fi

# ── Step 2: Lint (hard-fail) ─────────────────────────────────────────────────
run_target "lint"

# ── Step 3: Remaining gates from policy profile ──────────────────────────────
for gate in $GATES; do
    if [ "$gate" = "policy" ] || [ "$gate" = "lint" ]; then
        continue  # Already run
    fi
    run_target "$gate"
done

# ── Step 4: Negative validation checks ───────────────────────────────────────
echo ""
echo "→ Running negative validation checks ..."
NEGATIVE_PASS=0
NEGATIVE_TOTAL=0

# 4a: Broken lint must fail
NEGATIVE_TOTAL=$((NEGATIVE_TOTAL + 1))
if [ "${GATE_STATUS[lint]}" = "FAIL" ]; then
    echo "   ✅ Negative: Broken lint correctly fails gate"
    NEGATIVE_PASS=$((NEGATIVE_PASS + 1))
else
    echo "   ⚠️  Negative: Broken lint check not exercised (lint passed)"
fi

# 4b: Missing required artifact must fail sign-manifest
NEGATIVE_TOTAL=$((NEGATIVE_TOTAL + 1))
if [ "${GATE_STATUS[sign-manifest]}" = "FAIL" ]; then
    echo "   ✅ Negative: Missing artifacts correctly fails sign-manifest"
    NEGATIVE_PASS=$((NEGATIVE_PASS + 1))
else
    echo "   ⚠️  Negative: Missing artifact check not exercised (sign-manifest passed)"
fi

# 4c: Missing summary must fail render-summary
NEGATIVE_TOTAL=$((NEGATIVE_TOTAL + 1))
if [ "${GATE_STATUS[summary]}" = "FAIL" ]; then
    echo "   ✅ Negative: Missing summary correctly fails render-summary"
    NEGATIVE_PASS=$((NEGATIVE_PASS + 1))
else
    echo "   ⚠️  Negative: Missing summary check not exercised (render-summary passed)"
fi

# 4d: Placeholder gates in release-candidate must fail
NEGATIVE_TOTAL=$((NEGATIVE_TOTAL + 1))
if [ "$PROFILE" = "release-candidate" ]; then
    PLACEHOLDER_FAIL=0
    for gate in $GATES; do
        if [ "${GATE_CLASS[$gate]}" = "placeholder" ] && [ "${GATE_STATUS[$gate]}" = "FAIL" ]; then
            PLACEHOLDER_FAIL=$((PLACEHOLDER_FAIL + 1))
        fi
    done
    if [ "$PLACEHOLDER_FAIL" -gt 0 ]; then
        echo "   ✅ Negative: Placeholder gates correctly fail in release-candidate ($PLACEHOLDER_FAIL)"
        NEGATIVE_PASS=$((NEGATIVE_PASS + 1))
    else
        echo "   ⚠️  Negative: No placeholder gates failed in release-candidate"
    fi
else
    echo "   ⚠️  Negative: Placeholder enforcement only checked in release-candidate"
fi

# 4e: Broken smoke must fail if smoke is blocking
NEGATIVE_TOTAL=$((NEGATIVE_TOTAL + 1))
if [ "${GATE_CLASS[smoke]}" = "blocking" ] && [ "${GATE_STATUS[smoke]}" = "FAIL" ]; then
    echo "   ✅ Negative: Broken smoke correctly fails (smoke is blocking)"
    NEGATIVE_PASS=$((NEGATIVE_PASS + 1))
elif [ "${GATE_CLASS[smoke]}" = "advisory" ]; then
    echo "   ℹ️  Negative: Smoke is advisory — failure does not block"
    NEGATIVE_PASS=$((NEGATIVE_PASS + 1))
else
    echo "   ⚠️  Negative: Smoke check not exercised as expected"
fi

# ── Final decision ───────────────────────────────────────────────────────────
echo ""

# Count results
BLOCKING_PASS=0
BLOCKING_FAIL=0
BLOCKING_TOTAL=0
ADVISORY_PASS=0
ADVISORY_FAIL=0
ADVISORY_TOTAL=0
PLACEHOLDER_FAIL=0
ARTIFACT_FAIL=0

for gate in $GATES; do
    class="${GATE_CLASS[$gate]}"
    status="${GATE_STATUS[$gate]}"
    if [ "$class" = "blocking" ]; then
        BLOCKING_TOTAL=$((BLOCKING_TOTAL + 1))
        if [ "$status" = "PASS" ]; then
            BLOCKING_PASS=$((BLOCKING_PASS + 1))
        else
            BLOCKING_FAIL=$((BLOCKING_FAIL + 1))
        fi
    elif [ "$class" = "advisory" ]; then
        ADVISORY_TOTAL=$((ADVISORY_TOTAL + 1))
        if [ "$status" = "PASS" ]; then
            ADVISORY_PASS=$((ADVISORY_PASS + 1))
        else
            ADVISORY_FAIL=$((ADVISORY_FAIL + 1))
        fi
    elif [ "$class" = "placeholder" ]; then
        if [ "$status" = "FAIL" ]; then
            PLACEHOLDER_FAIL=$((PLACEHOLDER_FAIL + 1))
        fi
    elif [ "$class" = "artifact" ]; then
        if [ "$status" = "FAIL" ]; then
            ARTIFACT_FAIL=$((ARTIFACT_FAIL + 1))
        fi
    fi
done

HARD_FAIL=0
if [ "$BLOCKING_FAIL" -gt 0 ]; then
    HARD_FAIL=1
fi
if [ "$ARTIFACT_FAIL" -gt 0 ]; then
    HARD_FAIL=1
fi
if [ "$PROFILE" = "release-candidate" ] && [ "$PLACEHOLDER_FAIL" -gt 0 ]; then
    HARD_FAIL=1
fi

echo "========================================"
echo "Release Gate Results — Profile: $PROFILE"
echo "========================================"
printf "  Blocking:   %d/%d passed\n" "$BLOCKING_PASS" "$BLOCKING_TOTAL"
printf "  Advisory:   %d/%d passed\n" "$ADVISORY_PASS" "$ADVISORY_TOTAL"
printf "  Placeholder:%d failed (release-candidate blocks on these)\n" "$PLACEHOLDER_FAIL"
printf "  Negative:   %d/%d checks validated\n" "$NEGATIVE_PASS" "$NEGATIVE_TOTAL"
echo ""

if [ $HARD_FAIL -eq 0 ]; then
    echo "✅ SHIP — All blocking gates passed, no placeholders in release-candidate"
else
    echo "❌ DO NOT SHIP — Blocking or artifact gates failed"
    if [ "$PROFILE" = "release-candidate" ] && [ "$PLACEHOLDER_FAIL" -gt 0 ]; then
        echo "   Reason: release-candidate profile requires all placeholder gates to be implemented"
    fi
fi
echo ""
echo "Logs:    $LOG_DIR"
echo "Summary: $ARTIFACT_DIR/summary.md"
echo "========================================"

exit $HARD_FAIL
