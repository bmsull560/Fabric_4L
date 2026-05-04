#!/usr/bin/env bash
set -euo pipefail

# Sprint 2 launch-readiness gate.
# This script intentionally composes existing layer/API-contract checks instead
# of bypassing Fabric_4L layer boundaries or duplicating business logic.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

export TESTING="${TESTING:-true}"
export ENVIRONMENT="${ENVIRONMENT:-testing}"
export PYTHONPATH="${ROOT_DIR}/packages/shared/src:${ROOT_DIR}:${PYTHONPATH:-}"

run_step() {
  local label="$1"
  shift
  echo "→ ${label}"
  "$@"
}

run_root_pytest() {
  python -m pytest --tb=short -q -n 0 "$@"
}

run_step "Standalone API production-safety, durable persistence, and fail-closed provider checks" \
  bash -c 'cd services/api && TESTING=true ENVIRONMENT=testing python -m pytest --tb=short -q -n 0 app/tests/test_auth_enforcement.py app/tests/test_production_safety.py app/tests/test_i03_durable_persistence_and_llm.py'

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

run_step "Shared tenant context contract and import-boundary checks" \
  run_root_pytest \
    tests/context/test_tenant_context_contract.py \
    tests/contract/test_shared_import_boundary.py

run_step "OpenAPI contract drift check" \
  make --no-print-directory contract-drift

run_step "Frontend contract tests and placeholder guard" \
  bash -c 'cd apps/web && pnpm exec vitest run src/api/__tests__/contract && node scripts/security/assert-no-placeholder-contract-tests.mjs'

run_step "Critical E2E skip-valve guard" \
  bash -c 'cd apps/web && node scripts/security/assert-no-skipped-critical-e2e.mjs'

run_step "Kubernetes workload hardening checks" \
  run_root_pytest \
    tests/k8s/test_security_policies.py \
    tests/k8s/test_workload_validation.py

echo "✅ mandatory-security-regression gate passed"
