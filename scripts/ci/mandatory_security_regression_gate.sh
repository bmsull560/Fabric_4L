#!/usr/bin/env bash
set -euo pipefail

# Sprint 4 launch-readiness gate.
# This script intentionally composes existing layer/API-contract checks instead
# of bypassing Fabric_4L layer boundaries or duplicating business logic.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

export TESTING="${TESTING:-true}"
export ENVIRONMENT="${ENVIRONMENT:-testing}"
export PYTHONPATH="${ROOT_DIR}/packages/shared/src:${ROOT_DIR}:${PYTHONPATH:-}"

# Repo-relative artifact directory for cross-platform support
# Override via FABRIC_AUDIT_DIR environment variable for CI customization
FABRIC_AUDIT_DIR="${FABRIC_AUDIT_DIR:-.fabric/audit}"
AUDIT_DIR="${ROOT_DIR}/${FABRIC_AUDIT_DIR}"
mkdir -p "${AUDIT_DIR}/security_regression_gate"

# Test mode for regression testing - skips expensive operations
FABRIC_GATE_TEST_MODE="${FABRIC_GATE_TEST_MODE:-0}"

run_step() {
  local label="$1"
  shift
  echo "→ ${label}"
  "$@"
}

run_root_pytest() {
  python -m pytest --tb=short -q -n 0 "$@"
}

# Evidence logging functions
log_evidence_start() {
  local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  local git_sha=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
  local branch=$(git branch --show-current 2>/dev/null || echo "unknown")

  cat > "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.results.json" << EOF
{
  "timestamp": "${timestamp}",
  "git_sha": "${git_sha}",
  "branch": "${branch}",
  "os": "$(uname -s)",
  "gate_version": "1.1.0",
  "test_mode": ${FABRIC_GATE_TEST_MODE},
  "suites": [],
  "status": "in_progress"
}
EOF

  echo "# Mandatory Security Regression Gate Evidence" > "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "- **Timestamp**: ${timestamp}" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "- **Git SHA**: ${git_sha}" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "- **Branch**: ${branch}" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "- **OS**: $(uname -s)" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "- **Test Mode**: ${FABRIC_GATE_TEST_MODE}" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "## Check Results" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "| Check | Command | Required | Result | Evidence |" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "|-------|---------|----------|--------|----------|" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
}

log_suite_result() {
  local check_name="$1"
  local command="$2"
  local required="$3"
  local result="$4"
  local evidence="$5"

  # Append to JSON
  local temp_file=$(mktemp)
  jq --arg name "${check_name}" \
     --arg cmd "${command}" \
     --arg req "${required}" \
     --arg res "${result}" \
     --arg evi "${evidence}" \
     '.suites += [{"name": $name, "command": $cmd, "required": $req, "result": $res, "evidence": $evi}]' \
     "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.results.json" > "${temp_file}"
  mv "${temp_file}" "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.results.json"

  # Append to summary table
  echo "| ${check_name} | \`${command}\` | ${required} | ${result} | ${evidence} |" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
}

log_evidence_complete() {
  local exit_code=$1
  local status="PASS"
  if [[ ${exit_code} -ne 0 ]]; then
    status="FAIL"
  fi

  # Check if jq is available for JSON logging
  if command -v jq &> /dev/null; then
    local temp_file=$(mktemp)
    jq --arg status "${status}" \
       --arg exit_code "${exit_code}" \
       '.status = $status | .exit_code = ($exit_code | tonumber)' \
       "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.results.json" > "${temp_file}"
    mv "${temp_file}" "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.results.json"
  fi

  echo "" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "## Final Result" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "**Status**: ${status}" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "**Exit Code**: ${exit_code}" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
  echo "**Recommendation**: ${status}" >> "${AUDIT_DIR}/security_regression_gate/mandatory_security_regression_gate.summary.md"
}

# Required test suites - gate fails if any of these are missing
# These are file paths only (no :: pytest syntax) for existence checking
REQUIRED_SUITES=(
  "services/api/app/tests/test_auth_enforcement.py"
  "services/api/app/tests/test_production_safety.py"
  "services/api/app/tests/test_i03_durable_persistence_and_llm.py"
  "tests/security/test_auth_boundaries.py"
  "tests/security/test_auth_source_validation.py"
  "tests/security/test_jwt_config_validation.py"
  "tests/security/test_tenant_boundary_fails_closed.py"
  "tests/security/test_cross_tenant_api.py"
  "tests/security/test_tenant_mismatch.py"
  "tests/security/test_privileged_audit.py"
  "tests/security/test_rate_limit_safety.py"
  "tests/context/test_tenant_context_contract.py"
  "tests/contract/test_shared_import_boundary.py"
  "services/layer2-extraction/tests/test_production_fail_closed_i02.py"
  "services/layer5-ground-truth/tests/test_production_fail_closed_i02.py"
  "tests/k8s/test_security_policies.py"
  "tests/k8s/test_workload_validation.py"
)

# Fail-closed check: verify all required suites exist
check_required_suites() {
  local missing=()
  for suite in "${REQUIRED_SUITES[@]}"; do
    if [[ ! -f "${ROOT_DIR}/${suite}" ]]; then
      missing+=("${suite}")
    fi
  done

  if [[ ${#missing[@]} -gt 0 ]]; then
    echo "❌ ERROR: Required test suites missing:"
    for suite in "${missing[@]}"; do
      echo "   - ${suite}"
    done
    echo "Gate cannot proceed without required suites."
    exit 1
  fi
}

# Dry-run modes for testing
if [[ "${1:-}" == "--list-required" ]]; then
  for suite in "${REQUIRED_SUITES[@]}"; do
    echo "${suite}"
  done
  exit 0
fi

if [[ "${1:-}" == "--verify-required-only" ]]; then
  check_required_suites
  echo "✅ All required suites present"
  exit 0
fi

# Main gate execution - fail-closed check first
check_required_suites

# Initialize evidence logging
log_evidence_start

# Trap to ensure evidence is logged even on failure
trap 'log_evidence_complete $?' EXIT

run_step "Standalone API production-safety, durable persistence, and fail-closed provider checks" \
  bash -c 'cd services/api && TESTING=true ENVIRONMENT=testing python -m pytest --tb=short -q -n 0 app/tests/test_auth_enforcement.py app/tests/test_production_safety.py app/tests/test_i03_durable_persistence_and_llm.py'
log_suite_result "I-02/I-03 API Production Safety" "pytest app/tests/test_auth_enforcement.py test_production_safety.py test_i03_durable_persistence_and_llm.py" "Yes" "PASS" "✓"

run_step "Tenant-boundary and auth/security regression checks" \
  run_root_pytest \
    tests/security/test_auth_boundaries.py \
    tests/security/test_auth_source_validation.py \
    tests/security/test_jwt_config_validation.py \
    tests/security/test_tenant_boundary_fails_closed.py \
    tests/security/test_cross_tenant_api.py \
    tests/security/test_tenant_mismatch.py \
    tests/security/test_privileged_audit.py \
    tests/security/test_rate_limit_safety.py::TestMultiWorkerRateLimitSafety
log_suite_result "Tenant/Auth Security Regression" "pytest tests/security/*" "Yes" "PASS" "✓"

run_step "Shared tenant context contract and import-boundary checks" \
  run_root_pytest \
    tests/context/test_tenant_context_contract.py \
    tests/contract/test_shared_import_boundary.py
log_suite_result "Tenant Context Contract" "pytest tests/context/test_tenant_context_contract.py tests/contract/test_shared_import_boundary.py" "Yes" "PASS" "✓"

if [[ "${FABRIC_GATE_TEST_MODE}" != "1" ]]; then
  run_step "OpenAPI contract drift check" \
    make --no-print-directory contract-drift
  log_suite_result "OpenAPI Contract Drift" "make contract-drift" "Yes" "PASS" "✓"

  run_step "Frontend contract tests and placeholder guard" \
    bash -c 'cd apps/web && pnpm exec vitest run src/api/__tests__/contract && node scripts/security/assert-no-placeholder-contract-tests.mjs'
  log_suite_result "Frontend Contract Tests" "vitest + placeholder guard" "Yes" "PASS" "✓"

  run_step "Critical E2E skip-valve guard" \
    bash -c 'cd apps/web && node scripts/security/assert-no-skipped-critical-e2e.mjs'
  log_suite_result "Critical E2E Skip-Valve" "assert-no-skipped-critical-e2e.mjs" "Yes" "PASS" "✓"
else
  echo "→ [TEST MODE] Skipping OpenAPI contract drift check"
  echo "→ [TEST MODE] Skipping frontend contract tests"
  echo "→ [TEST MODE] Skipping critical E2E skip-valve guard"
  log_suite_result "OpenAPI Contract Drift" "make contract-drift" "Yes" "SKIPPED" "⊘"
  log_suite_result "Frontend Contract Tests" "vitest + placeholder guard" "Yes" "SKIPPED" "⊘"
  log_suite_result "Critical E2E Skip-Valve" "assert-no-skipped-critical-e2e.mjs" "Yes" "SKIPPED" "⊘"
fi

run_step "Kubernetes workload hardening checks" \
  run_root_pytest \
    tests/k8s/test_security_policies.py \
    tests/k8s/test_workload_validation.py
log_suite_result "Kubernetes Hardening" "pytest tests/k8s/*" "Yes" "PASS" "✓"

run_step "I-02 production fail-closed checks - Layer 2 (Extraction)" \
  bash -c 'cd services/layer2-extraction && python -m pytest --tb=short -q -n 0 tests/test_production_fail_closed_i02.py'
log_suite_result "I-02 Layer 2 Production Fail-Closed" "pytest tests/test_production_fail_closed_i02.py" "Yes" "PASS" "✓"

run_step "I-02 production fail-closed checks - Layer 5 (Ground Truth)" \
  bash -c 'cd services/layer5-ground-truth && python -m pytest --tb=short -q -n 0 tests/test_production_fail_closed_i02.py'
log_suite_result "I-02 Layer 5 Production Fail-Closed" "pytest tests/test_production_fail_closed_i02.py" "Yes" "PASS" "✓"

echo "✅ mandatory-security-regression gate passed"
echo "📦 Evidence written to: ${AUDIT_DIR}/security_regression_gate/"
