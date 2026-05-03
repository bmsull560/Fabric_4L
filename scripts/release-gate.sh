#!/usr/bin/env bash
# release-gate.sh — 4-layer quality gate sequence
#
# Runs all required checks before a production deployment:
#   Layer 1 — Core quality (lint, typecheck, unit tests)
#   Layer 2 — Agent behavior regression (evals)
#   Layer 3 — User-journey E2E (Playwright + backend contracts)
#   Layer 4 — Performance & reliability (k6 load tests)
#
# Usage:
#   bash scripts/release-gate.sh [profile]
#
# Profiles:
#   full    — all 4 layers (default)
#   fast    — layers 1 + 3 only (skip evals and load tests)
#   ci      — layers 1 + 3 with CI=true set for Playwright (enables forbidOnly,
#             retries=2, workers=2, and JUnit output to e2e-results/junit.xml
#             as configured in playwright.config.ts)
#
# Exit codes:
#   0 — all gates passed
#   1 — one or more gates failed (check output for details)

set -euo pipefail

PROFILE="${1:-full}"
FAILED_GATES=()

log()  { echo "[release-gate] $*"; }
pass() { echo "[release-gate] ✅  $1"; }
fail() { echo "[release-gate] ❌  $1"; FAILED_GATES+=("$1"); }

# Export CI=true when running the ci profile so Playwright picks up its CI
# behaviour (forbidOnly, retries, reduced workers, JUnit reporter output).
if [[ "${PROFILE}" == "ci" ]]; then
  export CI=true
fi

log "Profile: ${PROFILE}"
log "Starting release gate sequence..."
echo ""

# ── Layer 1: Core Quality ─────────────────────────────────────────────────────

log "Layer 1: Core quality gate (lint + typecheck + unit tests)"

if make lint 2>&1; then
  pass "lint"
else
  fail "lint"
fi

if make typecheck 2>&1; then
  pass "typecheck"
else
  fail "typecheck"
fi

if make test-frontend 2>&1; then
  pass "frontend unit tests"
else
  fail "frontend unit tests"
fi

if make contract-tests 2>&1; then
  pass "contract tests"
else
  fail "contract tests"
fi

# ── Layer 2: Agent Behavior Regression ───────────────────────────────────────

if [[ "${PROFILE}" == "full" ]]; then
  log "Layer 2: Agent behavior regression (evals)"

  if make evals 2>&1; then
    pass "evals"
  else
    fail "evals"
  fi
else
  log "Layer 2: Skipped (profile=${PROFILE})"
fi

# ── Layer 3: User-Journey E2E ─────────────────────────────────────────────────

log "Layer 3: User-journey E2E (Playwright + backend contracts)"

if make test-e2e-contracts 2>&1; then
  pass "e2e contract tests"
else
  fail "e2e contract tests"
fi

if make test-e2e-journeys 2>&1; then
  pass "e2e journey tests"
else
  fail "e2e journey tests"
fi

if make test-backend-contracts 2>&1; then
  pass "backend contract assertions"
else
  fail "backend contract assertions"
fi

# ── Layer 4: Performance & Reliability ───────────────────────────────────────

if [[ "${PROFILE}" == "full" ]]; then
  log "Layer 4: Performance & reliability (k6 load tests)"

  if make perf-test-journeys 2>&1; then
    pass "journey load tests"
  else
    fail "journey load tests"
  fi
else
  log "Layer 4: Skipped (profile=${PROFILE})"
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
if [[ ${#FAILED_GATES[@]} -eq 0 ]]; then
  log "✅  All gates passed — ready to deploy"
  exit 0
else
  log "❌  ${#FAILED_GATES[@]} gate(s) failed:"
  for gate in "${FAILED_GATES[@]}"; do
    echo "     - ${gate}"
  done
  exit 1
fi
