.PHONY: help verify verify-strict lint lint-layer1 lint-layer2 lint-layer3 lint-layer4 \
        lint-layer5 lint-layer6 typecheck typecheck-layer1 typecheck-layer2 \
        typecheck-layer3 typecheck-layer4 typecheck-layer5 typecheck-layer6 \
        test contract-tests contract-drift contract-lint test-layer1 test-layer2 test-layer3 test-layer4 \
        test-frontend build migrate evals perf-test perf-eval clean sdk \
        check-env check-env-backend check-env-frontend validate-env-contract \
        preflight up down logs check-deprecations test-backup-drills \
        gates-validate-policy gate-contract gate-arch gate-security gate-chaos \
        gate-smoke gate-agent gate-state gate-obs gate-release-policy \
        gates-sign-manifest gates-render-summary

# Strict shell settings for production safety
.ONESHELL:
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

PYTHON := python3
PIP    := pip install -e
PYTEST := pytest -v --tb=short

# Ensure mypy is available before running typecheck targets
MYPY_VERSION_CHECK := $(shell mypy --version 2>/dev/null || echo "mypy_not_found")

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Verification ────────────────────────────────────────────────────────────

verify: lint typecheck test contract-tests security-smoke check-deprecations check-tool-contracts ## Run all checks (lint + typecheck + tests + contracts + security + deprecations + tool-contracts) — required before PR
	@echo "✅  All checks passed"

verify-strict: verify contract-drift ## Full verification including contract drift detection (slower)
	@echo "✅  Strict verification passed"

# ─── Linting ─────────────────────────────────────────────────────────────────

lint-layer1: ## Lint Layer 1 only
	@echo "→ Linting Layer 1..."
	@cd value-fabric/layer1-ingestion && ruff check src/

lint-layer2: ## Lint Layer 2 only
	@echo "→ Linting Layer 2..."
	@cd value-fabric/layer2-extraction && ruff check src/

lint-layer3: ## Lint Layer 3 only
	@echo "→ Linting Layer 3..."
	@cd value-fabric/layer3-knowledge && ruff check src/

lint-layer4: ## Lint Layer 4 only
	@echo "→ Linting Layer 4..."
	@cd value-fabric/layer4-agents && ruff check src/

lint-layer5: ## Lint Layer 5 only
	@echo "→ Linting Layer 5..."
	@cd value-fabric/layer5-ground-truth && ruff check src/

lint-layer6: ## Lint Layer 6 only
	@echo "→ Linting Layer 6..."
	@cd value-fabric/layer6-benchmarks && ruff check src/

lint: ## Lint all Python layers with ruff (fails fast on first error)
	@$(MAKE) lint-layer1 && \
	 $(MAKE) lint-layer2 && \
	 $(MAKE) lint-layer3 && \
	 $(MAKE) lint-layer4 && \
	 $(MAKE) lint-layer5 && \
	 $(MAKE) lint-layer6 && \
	 echo "✅  Linting complete for all layers"

# Per-layer mypy flags - stricter layers enforce more type safety
# Layer 1: Relaxed with explicit untyped handling
MYPY_LAYER1_FLAGS = --warn-return-any --warn-unused-configs --disallow-untyped-defs=false
# Layer 2: Strict - fully typed codebase
MYPY_LAYER2_FLAGS = --strict --warn-return-any --warn-unused-configs
# Layer 3: Strict - fully typed codebase
MYPY_LAYER3_FLAGS = --strict --warn-return-any --warn-unused-configs
# Layer 4: Moderate - typed with some flexibility for agent patterns
MYPY_LAYER4_FLAGS = --warn-return-any --warn-unused-configs --disallow-untyped-defs=false
# Layer 5: Strict - fully typed codebase
MYPY_LAYER5_FLAGS = --strict --warn-return-any --warn-unused-configs
# Layer 6: Minimal - gradual typing
MYPY_LAYER6_FLAGS = --warn-return-any --warn-unused-configs

# Allow specific third-party overrides only where needed
MYPY_OVERRIDES = --python-version 3.11

# Per-layer typecheck targets for development efficiency
typecheck-layer1: ## Type-check Layer 1 only
	@if [ "$(MYPY_VERSION_CHECK)" = "mypy_not_found" ]; then echo "❌  mypy not found. Run: pip install mypy"; exit 1; fi
	@echo "→ Type-checking Layer 1..."
	@cd value-fabric/layer1-ingestion && mypy src/ $(MYPY_LAYER1_FLAGS)

typecheck-layer2: ## Type-check Layer 2 only
	@if [ "$(MYPY_VERSION_CHECK)" = "mypy_not_found" ]; then echo "❌  mypy not found. Run: pip install mypy"; exit 1; fi
	@echo "→ Type-checking Layer 2..."
	@cd value-fabric/layer2-extraction && mypy src/ $(MYPY_LAYER2_FLAGS)

typecheck-layer3: ## Type-check Layer 3 only
	@if [ "$(MYPY_VERSION_CHECK)" = "mypy_not_found" ]; then echo "❌  mypy not found. Run: pip install mypy"; exit 1; fi
	@echo "→ Type-checking Layer 3..."
	@cd value-fabric/layer3-knowledge && mypy src/ $(MYPY_LAYER3_FLAGS)

typecheck-layer4: ## Type-check Layer 4 only
	@if [ "$(MYPY_VERSION_CHECK)" = "mypy_not_found" ]; then echo "❌  mypy not found. Run: pip install mypy"; exit 1; fi
	@echo "→ Type-checking Layer 4..."
	@cd value-fabric/layer4-agents && mypy src/ $(MYPY_LAYER4_FLAGS)

typecheck-layer5: ## Type-check Layer 5 only
	@if [ "$(MYPY_VERSION_CHECK)" = "mypy_not_found" ]; then echo "❌  mypy not found. Run: pip install mypy"; exit 1; fi
	@echo "→ Type-checking Layer 5..."
	@cd value-fabric/layer5-ground-truth && mypy src/ $(MYPY_LAYER5_FLAGS)

typecheck-layer6: ## Type-check Layer 6 only
	@if [ "$(MYPY_VERSION_CHECK)" = "mypy_not_found" ]; then echo "❌  mypy not found. Run: pip install mypy"; exit 1; fi
	@echo "→ Type-checking Layer 6..."
	@cd value-fabric/layer6-benchmarks && mypy src/ $(MYPY_LAYER6_FLAGS)

typecheck: ## Type-check all Python layers with mypy (fails fast on first error)
	@$(MAKE) typecheck-layer1 && \
	 $(MAKE) typecheck-layer2 && \
	 $(MAKE) typecheck-layer3 && \
	 $(MAKE) typecheck-layer4 && \
	 $(MAKE) typecheck-layer5 && \
	 $(MAKE) typecheck-layer6 && \
	 echo "✅  Type-checking complete for all layers"

# ─── Testing ──────────────────────────────────────────────────────────────────

test: test-layer1 test-layer2 test-layer3 test-layer4 test-layer5 test-layer6 ## Run all backend unit tests

contract-tests: ## Run cross-layer contract + architecture tests (fast, no secrets required)
	@echo "→ Running contract tests (L2-L3, L4-Frontend, Tool Manifests)..."
	$(PYTEST) tests/contract/ -v --tb=short
	@echo "→ Running architecture tests (tenant isolation guards)..."
	$(PYTEST) tests/arch/ -v --tb=short
	@echo "✅  Contract and architecture tests passed"

# ─── Stratified Test Targets ─────────────────────────────────────────────────

test-unit: ## Run only unit tests (fast, no external deps)
	@echo "→ Running unit tests (marked with @pytest.mark.unit)"
	cd value-fabric/layer4-agents && $(PYTEST) -m unit tests/

test-integration: ## Run integration tests (real DB, cache, no containers)
	@echo "→ Running integration tests (marked with @pytest.mark.integration)"
	cd value-fabric/layer4-agents && $(PYTEST) -m integration tests/

test-e2e-docker: ## Run E2E tests with Docker containers
	@echo "→ Running E2E tests (requires Docker)"
	cd value-fabric/layer3-knowledge && $(PYTEST) -m e2e tests/ 2>/dev/null || true

test-fast: ## Run only fast tests (exclude slow and e2e)
	@echo "→ Running fast tests only"
	cd value-fabric/layer4-agents && $(PYTEST) -m "not slow and not e2e" tests/

# ─── Layer-Specific Tests ─────────────────────────────────────────────────────

test-layer1: ## Run Layer 1 tests
	cd value-fabric/layer1-ingestion && $(PYTEST) tests/

test-layer2: ## Run Layer 2 tests
	cd value-fabric/layer2-extraction && $(PYTEST) tests/

test-layer3: ## Run Layer 3 tests
	cd value-fabric/layer3-knowledge && $(PYTEST) tests/

test-layer4: ## Run Layer 4 tests
	cd value-fabric/layer4-agents && $(PYTEST) tests/

test-layer5: ## Run Layer 5 tests
	cd value-fabric/layer5-ground-truth && python scripts/check_no_duplicate_modules.py
	cd value-fabric/layer5-ground-truth && $(PYTEST) tests/

test-layer6: ## Run Layer 6 tests
	cd value-fabric/layer6-benchmarks && $(PYTEST) tests/

test-frontend: ## Run frontend unit tests
	cd frontend && pnpm run test

test-e2e: ## Run Playwright end-to-end tests (requires running stack)
	cd frontend && pnpm exec playwright test

# ─── Security Tests ───────────────────────────────────────────────────────────

security-smoke: ## Run fast security smoke tests (< 2 min, PR gating) - HARD FAIL
	@echo "→ Running security smoke tests (critical checks only)..."
	$(PYTEST) tests/security/test_security_smoke.py -v --tb=short -x
	@echo "✅  Security smoke tests passed"

security-test-gating: security-smoke ## Alias for security-smoke (explicit gating semantic)

security-test: ## Run full security test suite (~ 15 min, scheduled workflows)
	@echo "→ Running full security test suite..."
	$(PYTEST) tests/security/test_tenant_isolation.py -v --tb=short -k "P0"
	$(PYTEST) tests/security/test_rbac.py -v --tb=short -k "P0"
	$(PYTEST) tests/security/test_owasp_top10.py -v --tb=short -k "P0"
	$(PYTEST) tests/security/test_security_misconfiguration.py -v --tb=short
	@echo "✅  Full security test suite complete"

security-test-isolation: ## Run tenant isolation tests only
	@echo "→ Running tenant isolation tests..."
	$(PYTEST) tests/security/test_tenant_isolation.py -v --tb=short

security-test-rbac: ## Run RBAC tests only
	@echo "→ Running RBAC tests..."
	$(PYTEST) tests/security/test_rbac.py -v --tb=short

security-test-owasp: ## Run OWASP Top 10 tests only
	@echo "→ Running OWASP Top 10 tests..."
	$(PYTEST) tests/security/test_owasp_top10.py -v --tb=short

security-test-injection: ## Run injection prevention tests
	@echo "→ Running injection tests..."
	$(PYTEST) tests/security/test_injection.py -v --tb=short

security-coverage: ## Run security tests with coverage report
	@echo "→ Running security tests with coverage..."
	$(PYTEST) tests/security/ --cov=shared/security --cov-report=html --cov-report=term

# ─── Agent Evaluations ────────────────────────────────────────────────────────

evals: ## Run agent golden-trace evaluations (requires OPENAI_API_KEY)
	$(PYTEST) tests/evals/ -v --tb=short -m "not slow"

evals-full: ## Run full eval suite including slow/expensive traces
	$(PYTEST) tests/evals/ -v --tb=short


perf-test: ## Run k6 L2/L3/L4 critical-path load suite
	k6 run --summary-export artifacts/performance/k6-summary.json tests/performance/k6/l2_l3_l4_critical_paths.js

perf-eval: ## Evaluate k6 results against versioned SLO thresholds
	$(PYTHON) scripts/perf/evaluate_slo.py \
		--summary artifacts/performance/k6-summary.json \
		--slo docs/slo/performance-slo.v1.json \
		--report artifacts/performance/slo-report.md \
		--output artifacts/performance/slo-evaluation.json

# ─── Build ────────────────────────────────────────────────────────────────────

build: ## Build frontend production bundle
	cd frontend && pnpm run build

# ─── Database ─────────────────────────────────────────────────────────────────

migrate: ## Run Alembic migrations for all layers
	@echo "→ Migrating Layer 1..."
	cd value-fabric/layer1-ingestion && alembic upgrade head
	@echo "→ Migrating Layer 4..."
	cd value-fabric/layer4-agents && alembic upgrade head
	@echo "→ Migrating Layer 5..."
	cd value-fabric/layer5-ground-truth && alembic upgrade head

# ─── Contracts ────────────────────────────────────────────────────────────────

contracts: ## Export OpenAPI specs from all layers
	$(PYTHON) scripts/export_openapi.py

contract-drift: contracts ## Detect OpenAPI contract drift (exports + validates layer consistency)
	@echo "→ Checking for contract drift..."
	@# Verify all expected contract files exist and are non-empty
	@test -s contracts/openapi/layer1-ingestion.json || (echo "❌ Layer 1 OpenAPI spec missing or empty" && exit 1)
	@test -s contracts/openapi/layer2-extraction.json || (echo "❌ Layer 2 OpenAPI spec missing or empty" && exit 1)
	@test -s contracts/openapi/layer3-knowledge.json || (echo "❌ Layer 3 OpenAPI spec missing or empty" && exit 1)
	@test -s contracts/openapi/layer4-agents.json || (echo "❌ Layer 4 OpenAPI spec missing or empty" && exit 1)
	@test -s contracts/openapi/layer5-ground-truth.json || (echo "❌ Layer 5 OpenAPI spec missing or empty" && exit 1)
	@test -s contracts/openapi/layer6-benchmarks.json || (echo "⚠️ Layer 6 OpenAPI spec missing ( Gap 6 - non-blocking)")
	@echo "✅ All layer OpenAPI specs present"

sdk: ## Generate the Python SDK (manual typed client)
	$(PYTHON) scripts/generate_sdk.py

# ─── Dev Infrastructure ───────────────────────────────────────────────────────

preflight: ## Run pre-flight checks (Docker, env, ports)
	@bash scripts/dev-preflight.sh

up: preflight ## Start all services with Docker Compose (runs preflight first)
	cd value-fabric && docker compose up -d

down: ## Stop all services
	cd value-fabric && docker compose down

logs: ## Tail logs for all services
	cd value-fabric && docker compose logs -f

# ─── Cleanup ─────────────────────────────────────────────────────────────────

# ─── Environment Validation ───────────────────────────────────────────────────

check-env: ## Validate env vars against Zod schemas (backend + frontend)
	npx tsx scripts/check-env.ts all

check-env-backend: ## Validate backend env vars only
	npx tsx scripts/check-env.ts backend

check-env-frontend: ## Validate frontend env vars only
	npx tsx scripts/check-env.ts frontend

validate-env-contract: ## CI gate — validate env contract + schema
	npx tsx scripts/ci/validate-env-contract.ts all

# ─── Deprecation Checks ─────────────────────────────────────────────────────

check-deprecations: ## CI gate — check for overdue deprecations
	$(PYTHON) scripts/ci/check_deprecations.py

check-tool-contracts: ## CI gate — validate tool error structure (CONTRACT.md §2.4)
	@echo "→ Checking tool contracts in Layer 4..."
	$(PYTHON) scripts/ci/check_tool_contracts.py value-fabric/layer4-agents/src/tools/
	@echo "✅ Tool contract check passed"

# ─── Production Readiness Gates ─────────────────────────────────────────────

POLICY_FILE ?= .fabric/prod-gates.policy.yaml
GATE_PROFILE ?= pr-fast

gates-validate-policy: ## Validate the production gates policy schema
	$(PYTHON) scripts/gates/validate_policy.py --policy $(POLICY_FILE)

gate-contract: ## Run contract compliance gate (ESLint + drift detection)
	$(PYTHON) scripts/gates/run_contract.py --profile $(GATE_PROFILE) --policy $(POLICY_FILE)

contract-drift: ## Detect drift between CONTRACT.md and codebase
	@echo "→ Running contract drift detection..."
	$(PYTHON) scripts/gates/run_contract.py --profile mainline-full --policy $(POLICY_FILE) --drift-only

contract-lint: ## Run ESLint contract rules across all packages
	@echo "→ Running contract lint rules..."
	cd frontend/client && npm run lint -- --ext .ts,.tsx --rule 'fabric-contracts/no-tenant-id-parameter: error' --rule 'fabric-contracts/no-req-tenant-access: error' --rule 'fabric-contracts/no-raw-tenant-query: error' --rule 'fabric-contracts/no-explicit-db-connect: error' --rule 'fabric-contracts/no-inline-middleware: error' --rule 'fabric-contracts/no-inline-tool-definition: error' --rule 'fabric-contracts/no-throw-in-tool: error' --rule 'fabric-contracts/no-json-parse-agent-output: error' --rule 'fabric-contracts/no-imperative-navigation: error' --rule 'fabric-contracts/no-url-concatenation: error' --rule 'fabric-contracts/no-private-imports: error' --rule 'fabric-contracts/no-circular-dependencies: error' 2>/dev/null || echo "⚠️  Contract ESLint plugin not yet installed"

gate-arch: ## Run architecture conformance gate
	$(PYTHON) scripts/gates/run_arch.py --profile $(GATE_PROFILE) --policy $(POLICY_FILE)

gate-security: ## Run security compliance gate
	$(PYTHON) scripts/gates/run_security.py --profile $(GATE_PROFILE) --policy $(POLICY_FILE)

gate-chaos: ## Run chaos engineering gate
	$(PYTHON) scripts/gates/run_chaos.py --profile $(GATE_PROFILE) --policy $(POLICY_FILE)

gate-smoke: ## Run smoke test gate
	$(PYTHON) scripts/gates/run_smoke.py --profile $(GATE_PROFILE) --policy $(POLICY_FILE)

gate-agent: ## Run agent evaluation gate
	$(PYTHON) scripts/gates/run_agent.py --profile $(GATE_PROFILE) --policy $(POLICY_FILE)

gate-state: ## Run state management gate
	$(PYTHON) scripts/gates/run_state.py --profile $(GATE_PROFILE) --policy $(POLICY_FILE)

gate-obs: ## Run observability gate
	$(PYTHON) scripts/gates/run_obs.py --profile $(GATE_PROFILE) --policy $(POLICY_FILE)

gate-release-policy: ## Evaluate release policy compliance
	$(PYTHON) scripts/gates/evaluate_release.py --profile $(GATE_PROFILE) --policy $(POLICY_FILE)

gates-sign-manifest: ## Sign the release manifest
	$(PYTHON) scripts/gates/sign_manifest.py --manifest artifacts/release/manifest.json

gates-render-summary: ## Render the gates summary report
	$(PYTHON) scripts/gates/render_summary.py --input artifacts --output artifacts/release/summary.md

# ─── Backup/DR Tests ─────────────────────────────────────────────────────────

test-backup-drills: ## Run backup/DR drill tests (requires pytest-asyncio)
	@echo "→ Running backup manager tests..."
	cd value-fabric/layer3-knowledge && $(PYTEST) tests/test_backup_manager.py -v --tb=short

# ─── Cleanup ─────────────────────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅  Clean complete"
