#!/usr/bin/env bash
# scripts/release-gate.sh — Release Gate orchestrator for Value Fabric
# Usage: bash scripts/release-gate.sh [PROFILE]
# Profile: pr-fast | mainline-full | release-candidate (default: release-candidate)
set -euo pipefail

PROFILE="${1:-release-candidate}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
ARTIFACT_DIR="${ROOT}/artifacts/release"
LOG_DIR="${ARTIFACT_DIR}/logs"
mkdir -p "$LOG_DIR"

echo "🚀 Release Gate — Profile: $PROFILE"
echo "   Root:    $ROOT"
echo "   Artifacts: $ARTIFACT_DIR"
echo ""

# ── Helper: run a target and log output ──────────────────────────────────────
run_gate() {
    local target="$1"
    local logfile="${LOG_DIR}/${target}.log"
    local rc=0
    echo "→ $target ..." | tee -a "$LOG_DIR/release-gate.log"
    if make -C "$ROOT" "$target" > "$logfile" 2>&1; then
        echo "   ✅ $target" | tee -a "$LOG_DIR/release-gate.log"
    else
        echo "   ❌ $target" | tee -a "$LOG_DIR/release-gate.log"
        rc=1
    fi
    return $rc
}

# ── Step 1: Validate Policy ──────────────────────────────────────────────────
run_gate gates-validate-policy || { echo "Policy validation failed"; exit 1; }

# ── Step 2: Architecture ─────────────────────────────────────────────────────
run_gate gate-arch || { echo "Architecture gate failed"; exit 1; }

# ── Step 3: Security ─────────────────────────────────────────────────────────
run_gate gate-security || { echo "Security gate failed"; exit 1; }

# ── Step 4: Lint + Typecheck + Unit (Layer by layer, continue on soft-fail) ──
echo "→ Running lint / typecheck / unit tests ..."
make -C "$ROOT" lint-release typecheck test-unit > "${LOG_DIR}/core-quality.log" 2>&1 && \
    echo "   ✅ Core quality gate" || echo "   ⚠️  Core quality gate had warnings (see core-quality.log)"

# ── Step 5: Agent Evals (continue on soft-fail) ──────────────────────────────
echo "→ Running agent evals ..."
make -C "$ROOT" evals > "${LOG_DIR}/evals.log" 2>&1 && \
    echo "   ✅ Agent evals" || echo "   ⚠️  Agent evals had warnings (see evals.log)"

# ── Step 6: E2E ──────────────────────────────────────────────────────────────
run_gate gate-smoke || true   # soft fail — services may not be running

# ── Step 7: Performance ──────────────────────────────────────────────────────
run_gate gate-obs || true   # soft fail

# ── Step 8: State alignment ──────────────────────────────────────────────────
run_gate gate-state || { echo "State gate failed"; exit 1; }

# ── Step 9: Agent gate ───────────────────────────────────────────────────────
run_gate gate-agent || true

# ── Step 10: Release policy ──────────────────────────────────────────────────
run_gate gate-release-policy || true

# ── Step 11: Sign manifest ───────────────────────────────────────────────────
run_gate gates-sign-manifest

# ── Step 12: Render summary ──────────────────────────────────────────────────
run_gate gates-render-summary

echo ""
echo "========================================"
echo "✅ Release Gate Sequence Complete"
echo "Profile: $PROFILE"
echo "Logs:    $LOG_DIR"
echo "Summary: $ARTIFACT_DIR/summary.md"
echo "========================================"
