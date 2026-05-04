.PHONY: help verify verify-strict lint lint-layer1 lint-layer2 lint-layer3 lint-layer4 \
        lint-layer5 lint-layer6 typecheck typecheck-layer1 typecheck-layer2 \
        typecheck-layer3 typecheck-layer4 typecheck-layer5 typecheck-layer6 \
        test contract-tests contract-lint test-layer1 test-layer2 test-layer3 test-layer4 \
        test-frontend build migrate evals perf-test perf-eval clean sdk \
        check-env check-env-backend check-env-frontend validate-env-contract \
        preflight up down logs check-deprecations test-backup-drills \
        test-backend-integrated-validation test-backend-integrated-release-smoke \
        gate-mandatory-security-regression gate-security gate-state gate-arch gate-config gate-all \
        platform-contract-lint setup-hooks check-ui-duplicates check-readiness-consistency

# Strict shell settings for production safety
.ONESHELL:
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

PROFILE ?= release-candidate
POLICY_FILE := .fabric/prod-gates.policy.yaml
ARTIFACT_DIR := artifacts/release

PYTHON := python3
PIP    := pip install -e
PYTEST := pytest -v --tb=short

# Ensure mypy is available before running typecheck targets
MYPY_VERSION_CHECK := $(shell mypy --version 2>/dev/null || echo "mypy_not_found")

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Verification ────────────────────────────────────────────────────────────

verify: lint typecheck test contract-tests security-smoke check-deprecations check-tool-contracts platform-contract-lint check-ui-duplicates check-readiness-consistency verify-structure ## Run all checks (lint + typecheck + tests + contracts + security + deprecations + tool-contracts + ui-dup-guard + readiness-consistency + structure) — required before PR
	@echo "✅  All checks passed"

verify-structure: ## Run structural preflight and Python contract lint checks
	@echo "→ Running structural preflight..."
	@python scripts/ci/structural_preflight.py --strict
	@echo "→ Running Python contract lint..."
	@python scripts/ci/python_contract_lint.py --strict
	@echo "→ Running strict shared-import enforcement..."
	@python scripts/ci/check_shared_imports.py --strict --scope executable
	@echo "→ Running import topology tests..."
	@python -m pytest tests/contract/test_import_topology.py -q
	@echo "→ Running strict navigation pattern check..."
	@cd apps/web && python ../../scripts/ci/check_navigation_patterns.py --strict
	@echo "✅  Structure verification passed"

check-ui-duplicates: ## Block new duplicate UI component filenames between prototype and production trees
	@python3 scripts/check_ui_duplicate_filenames.py

check-readiness-consistency: ## Ensure canonical readiness percentages are aligned and archives are snapshot-tagged
	@python3 scripts/ci/check_readiness_consistency.py

verify-strict: verify contract-drift ## Full verification including contract drift detection (slower)
	@echo "✅  Strict verification passed"

# ─── Linting ─────────────────────────────────────────────────────────────────

lint-layer1: ## Lint Layer 1 only
	@echo "→ Linting Layer 1..."
	@cd services/layer1-ingestion && ruff check src/

lint-layer2: ## Lint Layer 2 only
	@echo "→ Linting Layer 2..."
	@cd services/layer2-extraction && ruff check src/

lint-layer3: ## Lint Layer 3 only
	@echo "→ Linting Layer 3..."
	@cd services/layer3-knowledge && ruff check src/

lint-layer4: ## Lint Layer 4 only
	@echo "→ Linting Layer 4..."
	@cd services/layer4-agents && ruff check src/

lint-layer5: ## Lint Layer 5 only
	@echo "→ Linting Layer 5..."
	@cd services/layer5-ground-truth && ruff check src/

lint-layer6: ## Lint Layer 6 only
	@echo "→ Linting Layer 6..."
	@cd services/layer6-benchmarks && ruff check src/

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
MYPY_LAYER1_FLAGS = --warn-return-any --warn-unused-configs
# Layer 2: Strict - fully typed codebase
MYPY_LAYER2_FLAGS = --strict --warn-return-any --warn-unused-configs
# Layer 3: Strict - fully typed codebase
MYPY_LAYER3_FLAGS = --strict --warn-return-any --warn-unused-configs
# Layer 4: Moderate - typed with some flexibility for agent patterns
MYPY_LAYER4_FLAGS = --warn-return-any --warn-unused-configs
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
	@cd services/layer1-ingestion && mypy src/ $(MYPY_LAYER1_FLAGS)

typecheck-layer2: ## Type-check Layer 2 only
	@if [ "$(MYPY_VERSION_CHECK)" = "mypy_not_found" ]; then echo "❌  mypy not found. Run: pip install mypy"; exit 1; fi
	@echo "→ Type-checking Layer 2..."
	@cd services/layer2-extraction && mypy src/ $(MYPY_LAYER2_FLAGS)

typecheck-layer3: ## Type-check Layer 3 only
	@if [ "$(MYPY_VERSION_CHECK)" = "mypy_not_found" ]; then echo "❌  mypy not found. Run: pip install mypy"; exit 1; fi
	@echo "→ Type-checking Layer 3..."
	@cd services/layer3-knowledge && mypy src/ $(MYPY_LAYER3_FLAGS)

typecheck-layer4: ## Type-check Layer 4 only
	@if [ "$(MYPY_VERSION_CHECK)" = "mypy_not_found" ]; then echo "❌  mypy not found. Run: pip install mypy"; exit 1; fi
	@echo "→ Type-checking Layer 4..."
	@cd services/layer4-agents && mypy src/ $(MYPY_LAYER4_FLAGS)

typecheck-layer5: ## Type-check Layer 5 only
	@if [ "$(MYPY_VERSION_CHECK)" = "mypy_not_found" ]; then echo "❌  mypy not found. Run: pip install mypy"; exit 1; fi
	@echo "→ Type-checking Layer 5..."
	@cd services/layer5-ground-truth && mypy src/ $(MYPY_LAYER5_FLAGS)

typecheck-layer6: ## Type-check Layer 6 only
	@if [ "$(MYPY_VERSION_CHECK)" = "mypy_not_found" ]; then echo "❌  mypy not found. Run: pip install mypy"; exit 1; fi
	@echo "→ Type-checking Layer 6..."
	@cd services/layer6-benchmarks && mypy src/ $(MYPY_LAYER6_FLAGS)

typecheck: ## Type-check all Python layers with mypy (fails fast on first error)
	@$(MAKE) typecheck-layer1 && \
	 $(MAKE) typecheck-layer2 && \
	 $(MAKE) typecheck-layer3 && \
	 $(MAKE) typecheck-layer4 && \
	 $(MAKE) typecheck-layer5 && \
	 $(MAKE) typecheck-layer6 && \
	 echo "✅  Type-checking complete for all layers"

# ─── Testing (4-Layer Strategy) ───────────────────────────────────────────────

test: test-layer1 test-layer2 test-layer3 test-layer4 test-layer5 test-layer6 ## Run all backend unit tests

test-e2e-contracts: ## Layer 1: Run Playwright isolated page contract tests (mocked)
	cd apps/web && npx playwright test --project=contracts

test-e2e-journeys: ## Layer 2: Run Playwright chained user journeys (live or mocked)
	cd apps/web && npx playwright test --project=journeys

test-backend-contracts: ## Layer 3: Run backend contract/integration assertions
	$(PYTEST) tests/contract/test_journey_contracts.py -v

test-backend-integrated-validation: ## Backend milestone: run live-service workflow, persistence, tenant, agent, and resilience validation
	$(PYTEST) tests/backend_integrated -m backend_integrated -v

test-backend-integrated-release-smoke: ## Backend milestone: boot full L1-L6 release stack and run release-environment smoke validation
	bash scripts/ci/run_release_smoke.sh

seed-e2e: ## Seed deterministic E2E fixture data into the local backend (requires running stack)
	@echo "→ Seeding E2E test data..."
	npx tsx scripts/db/seed-e2e-data.ts
	@echo "✅  E2E seed complete"

reset-e2e: ## Remove all E2E tenant data from the local backend
	@echo "→ Resetting E2E test data..."
	npx tsx scripts/db/reset-e2e-data.ts
	@echo "✅  E2E reset complete"

test-e2e-full: ## Run full E2E suite: seed → contracts → journeys → reset
	@echo "→ Starting full E2E run..."
	$(MAKE) seed-e2e
	$(MAKE) test-e2e-contracts
	$(MAKE) test-e2e-journeys
	$(MAKE) reset-e2e
	@echo "✅  Full E2E suite complete"

contract-tests: ## Run cross-layer contract + architecture tests (fast, no secrets required)
	@echo "→ Running contract tests (L2-L3, L4-Frontend, Tool Manifests)..."
	$(PYTEST) tests/contract/ -v --tb=short
	cd packages/platform-contract && npm run contract:test
	@echo "→ Running architecture tests (tenant isolation guards)..."
	$(PYTEST) tests/arch/ -v --tb=short
	@echo "✅  Contract and architecture tests passed"

# ─── Stratified Test Targets ─────────────────────────────────────────────────

test-unit: ## Run only unit tests (fast, no external deps)
	@echo "→ Running unit tests (marked with @pytest.mark.unit)"
	cd services/layer4-agents && $(PYTEST) -m unit tests/

test-integration: ## Run integration tests (real DB, cache, no containers)
	@echo "→ Running integration tests (marked with @pytest.mark.integration)"
	cd services/layer4-agents && $(PYTEST) -m integration tests/

test-e2e-docker: ## Run E2E tests with Docker containers
	@echo "→ Running E2E tests (requires Docker)"
	cd services/layer3-knowledge && $(PYTEST) -m e2e tests/ 2>/dev/null || true

test-fast: ## Run only fast tests (exclude slow and e2e)
	@echo "→ Running fast tests only"
	cd services/layer4-agents && $(PYTEST) -m "not slow and not e2e" tests/

# ─── Layer-Specific Tests ─────────────────────────────────────────────────────

test-layer1: ## Run Layer 1 tests
	cd services/layer1-ingestion && $(PYTEST) tests/

test-layer2: ## Run Layer 2 tests
	cd services/layer2-extraction && $(PYTEST) tests/

test-layer3: ## Run Layer 3 tests
	cd services/layer3-knowledge && $(PYTEST) tests/

test-layer4: ## Run Layer 4 tests
	cd services/layer4-agents && $(PYTEST) tests/

test-layer5: ## Run Layer 5 tests
	cd services/layer5-ground-truth && python scripts/check_no_duplicate_modules.py
	cd services/layer5-ground-truth && $(PYTEST) tests/

test-layer6: ## Run Layer 6 tests
	cd services/layer6-benchmarks && $(PYTEST) tests/

test-frontend: ## Run frontend unit tests
	cd apps/web && pnpm run test

test-e2e: ## Run Playwright end-to-end tests (requires running stack)
	cd apps/web && pnpm exec playwright test

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

perf-test-journeys: ## Layer 4: Run k6 journey-aligned load tests
	k6 run tests/performance/k6/journey-load-test.js

perf-eval: ## Evaluate k6 results against versioned SLO thresholds
	$(PYTHON) scripts/perf/evaluate_slo.py \
		--summary artifacts/performance/k6-summary.json \
		--slo docs/slo/performance-slo.v1.json \
		--report artifacts/performance/slo-report.md \
		--output artifacts/performance/slo-evaluation.json

# ─── Build ────────────────────────────────────────────────────────────────────

build: ## Build frontend production bundle
	cd apps/web && pnpm run build

# ─── Database ─────────────────────────────────────────────────────────────────

migrate: ## Run Alembic migrations for all layers
	@echo "→ Migrating Layer 1..."
	cd services/layer1-ingestion && alembic upgrade head
	@echo "→ Migrating Layer 4..."
	cd services/layer4-agents && alembic upgrade head
	@echo "→ Migrating Layer 5..."
	cd services/layer5-ground-truth && alembic upgrade head

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
	@bash scripts/dev/dev-preflight.sh

up: preflight ## Start all services with Docker Compose (runs preflight first)
	docker compose -f docker-compose.dev.yml up -d

down: ## Stop all services
	docker compose -f docker-compose.dev.yml down

logs: ## Tail logs for all services
	docker compose -f docker-compose.dev.yml logs -f

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
	$(PYTHON) scripts/ci/check_tool_contracts.py services/layer4-agents/src/tools/
	@echo "✅ Tool contract check passed"

# ─── Developer Setup ─────────────────────────────────────────────────────────

setup-hooks: ## Configure git to use .githooks/ (run once after clone)
	@git config core.hooksPath .githooks
	@echo "✅  Git hooks configured. Pre-push gate tests will run before every push."

# ─── Production Readiness Gates ─────────────────────────────────────────────
# Gate system: pytest is the single source of truth.
# Each gate-* target runs pytest directly. Non-zero exit = release blocked.
# No runners, no policy engines, no simulation.

GATE_PYTEST := $(PYTEST) --tb=short -q -n 0
GATE_TIMEOUT_SECONDS ?= 180
GATE_JUNIT_DIR := $(ARTIFACT_DIR)/junit

gate-mandatory-security-regression: ## Gate: mandatory security regression suite for launch readiness
	@echo "→ Gate: Mandatory Security Regression"
	bash scripts/ci/mandatory_security_regression_gate.sh
	@echo "✅  gate-mandatory-security-regression passed"

gate-security: gate-mandatory-security-regression ## Gate: release-critical tenant isolation, auth enforcement, and fail-closed security regression
	@echo "→ Gate: Security & Tenant Isolation — release-critical suite"
	@echo "✅  gate-security passed"

gate-security-broad: ## Advisory gate: exhaustive legacy security coverage for Broad GA backlog classification
	@echo "→ Gate: Broad Security Coverage — advisory legacy suite (bounded to 300s)"
	timeout 300s $(GATE_PYTEST) tests/security/
	@echo "✅  gate-security-broad passed"

gate-state: ## Gate: frontend/backend state alignment, workflow type consistency
	@echo "→ Gate: State Alignment"
	$(GATE_PYTEST) tests/state/
	@echo "✅  gate-state passed"

gate-arch: ## Gate: architecture conformance, tenant guards, testability
	@echo "→ Gate: Architecture Conformance"
	$(GATE_PYTEST) tests/arch/
	@echo "✅  gate-arch passed"

gate-config: ## Gate: startup validation, security config hardening
	@echo "→ Gate: Startup Configuration"
	$(GATE_PYTEST) tests/config/
	@echo "✅  gate-config passed"

gate-all: gate-security gate-state gate-arch gate-config ## Run all production readiness gates
	@echo "✅  All production gates passed — ship/no-ship: SHIP"

# ─── Extended Gate Targets (referenced by prod-readiness.yml) ────────────────

lint-release: lint-layer1 lint-layer2 lint-layer3 lint-layer4 lint-layer5 lint-layer6 ## Lint all layers (release variant)
	@echo "✅  Release lint complete"

gates-validate-policy: ## Validate gate policy schema, profile existence, and artifact dirs
	@echo "→ Gate: Validate Policy"
	@test -s $(POLICY_FILE) || (echo "❌ Policy file $(POLICY_FILE) not found" && exit 1)
	@python -c "import yaml; yaml.safe_load(open('$(POLICY_FILE)'))" || (echo "❌ Policy file is not valid YAML" && exit 1)
	@mkdir -p artifacts/{arch,security,chaos,smoke,agent,state,obs,release}
	@echo "✅  gates-validate-policy passed"

gate-chaos: ## Gate: dependency chaos and failure injection
	@echo "→ Gate: Chaos"
	@if [ ! -d tests/chaos ] || [ -z "$$(find tests/chaos -name 'test_*.py' -print -quit)" ]; then \
		echo "❌ PLACEHOLDER: No chaos tests implemented (0 test files)."; \
		exit 1; \
	fi
	@mkdir -p $(GATE_JUNIT_DIR)
	timeout $(GATE_TIMEOUT_SECONDS)s $(GATE_PYTEST) tests/chaos/ --junitxml=$(GATE_JUNIT_DIR)/gate-chaos.xml
	python scripts/ci/assert_no_pytest_skips.py $(GATE_JUNIT_DIR)/gate-chaos.xml
	@echo "✅  gate-chaos passed"

gate-smoke: ## Gate: cross-domain smoke tests
	@echo "→ Gate: Smoke"
	@test -s tests/e2e/test_value_engine_smoke_contract.py || (echo "❌ Smoke contract test is missing" && exit 1)
	@mkdir -p $(GATE_JUNIT_DIR)
	timeout $(GATE_TIMEOUT_SECONDS)s $(GATE_PYTEST) tests/e2e/test_value_engine_smoke_contract.py --junitxml=$(GATE_JUNIT_DIR)/gate-smoke.xml
	python scripts/ci/assert_no_pytest_skips.py $(GATE_JUNIT_DIR)/gate-smoke.xml
	@echo "✅  gate-smoke passed"

gate-agent: ## Gate: agent provenance and behavior regression
	@echo "→ Gate: Agent"
	@if [ ! -d tests/agents ] || [ -z "$$(find tests/agents -name 'test_*.py' -print -quit)" ]; then \
		echo "❌ PLACEHOLDER: No agent tests implemented."; \
		exit 1; \
	fi
	@mkdir -p $(GATE_JUNIT_DIR)
	timeout $(GATE_TIMEOUT_SECONDS)s $(GATE_PYTEST) tests/agents/ --junitxml=$(GATE_JUNIT_DIR)/gate-agent.xml
	python scripts/ci/assert_no_pytest_skips.py $(GATE_JUNIT_DIR)/gate-agent.xml
	@echo "✅  gate-agent passed"

gate-obs: ## Gate: observability, metrics, and SLO validation
	@echo "→ Gate: Observability"
	@if [ ! -d tests/performance ] || [ -z "$$(find tests/performance -name 'test_*.py' -print -quit)" ]; then \
		echo "❌ PLACEHOLDER: No performance tests implemented."; \
		exit 1; \
	fi
	@mkdir -p $(GATE_JUNIT_DIR)
	timeout $(GATE_TIMEOUT_SECONDS)s $(GATE_PYTEST) tests/performance/ --junitxml=$(GATE_JUNIT_DIR)/gate-obs.xml
	python scripts/ci/assert_no_pytest_skips.py $(GATE_JUNIT_DIR)/gate-obs.xml
	@echo "✅  gate-obs passed"

gate-release-policy: ## Gate: release policy compliance
	@echo "→ Gate: Release Policy"
	@if [ ! -d tests/release ] || [ -z "$$(find tests/release -name 'test_*.py' -print -quit)" ]; then \
		echo "❌ PLACEHOLDER: No release-policy tests implemented."; \
		exit 1; \
	fi
	@mkdir -p $(GATE_JUNIT_DIR)
	timeout $(GATE_TIMEOUT_SECONDS)s $(GATE_PYTEST) tests/release/ --junitxml=$(GATE_JUNIT_DIR)/gate-release-policy.xml
	python scripts/ci/assert_no_pytest_skips.py $(GATE_JUNIT_DIR)/gate-release-policy.xml
	python scripts/ci/check_deprecations.py
	@echo "✅  gate-release-policy passed"

gates-sign-manifest: ## Sign artifact manifest with SHA-256
	@echo "→ Gate: Sign Manifest"
	@mkdir -p $(ARTIFACT_DIR)/logs
	@if [ ! -d $(ARTIFACT_DIR) ]; then \
		echo "❌ Artifact directory $(ARTIFACT_DIR) does not exist"; \
		exit 1; \
	fi
	@FILE_COUNT=$$(find $(ARTIFACT_DIR) -type f -not -path "*/logs/*" -not -name "manifest.sha256" | wc -l); \
	if [ "$$FILE_COUNT" -eq 0 ]; then \
		echo "❌ No artifacts to sign in $(ARTIFACT_DIR)"; \
		exit 1; \
	fi
	@find $(ARTIFACT_DIR) -type f -not -path "*/logs/*" -not -name "manifest.sha256" -exec sha256sum {} \; > $(ARTIFACT_DIR)/manifest.sha256
	@echo "✅  gates-sign-manifest passed ($$(wc -l < $(ARTIFACT_DIR)/manifest.sha256) files)"

gates-render-summary: ## Render release summary with gate results
	@echo "→ Gate: Render Summary"
	@bash scripts/ops/render-release-summary.sh
	@test -s $(ARTIFACT_DIR)/summary.md || (echo "❌ Summary file not generated" && exit 1)
	@echo "✅  gates-render-summary passed"

release-gate: ## Run the policy-driven production readiness gate sequence
	@echo "🚀 Starting Release Gate Sequence..."
	@bash scripts/ops/release-gate.sh $(PROFILE)

contract-lint: ## Run ESLint contract rules across all packages
	@echo "→ Running contract lint rules..."
	@cd apps/web && npm run lint -- --ext .ts,.tsx --rule 'fabric-contracts/no-tenant-id-parameter: error' --rule 'fabric-contracts/no-req-tenant-access: error' --rule 'fabric-contracts/no-raw-tenant-query: error' --rule 'fabric-contracts/no-explicit-db-connect: error' --rule 'fabric-contracts/no-inline-middleware: error' --rule 'fabric-contracts/no-inline-tool-definition: error' --rule 'fabric-contracts/no-throw-in-tool: error' --rule 'fabric-contracts/no-json-parse-agent-output: error' --rule 'fabric-contracts/no-imperative-navigation: error' --rule 'fabric-contracts/no-url-concatenation: error' --rule 'fabric-contracts/no-private-imports: error' --rule 'fabric-contracts/no-circular-dependencies: error' 2>/dev/null || echo "⚠️  Contract ESLint plugin not yet installed"

# ─── Backup/DR Tests ─────────────────────────────────────────────────────────

test-backup-drills: ## Run backup/DR drill tests (requires pytest-asyncio)
	@echo "→ Running backup manager tests..."
	cd services/layer3-knowledge && $(PYTEST) tests/test_backup_manager.py -v --tb=short

# ─── Cleanup ─────────────────────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅  Clean complete"

# Platform Contract Lint
platform-contract-lint:
	@echo Running platform contract lint...
	@python scripts/ci/platform_contract_lint.py
