.PHONY: help verify lint typecheck test contract-tests test-layer1 test-layer2 test-layer3 test-layer4 \
        test-frontend build migrate evals perf-test perf-eval clean sdk \
        check-env check-env-backend check-env-frontend validate-env-contract \
        preflight up down logs

PYTHON := python3
PIP    := pip install -e
PYTEST := pytest -v --tb=short

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Verification ────────────────────────────────────────────────────────────

verify: lint typecheck test contract-tests ## Run all checks (lint + typecheck + tests + contracts) — required before PR
	@echo "✅  All checks passed"

# ─── Linting ─────────────────────────────────────────────────────────────────

lint: ## Lint all Python layers with ruff
	@echo "→ Linting Layer 1..."
	cd value-fabric/layer1-ingestion && ruff check src/
	@echo "→ Linting Layer 2..."
	cd value-fabric/layer2-extraction && ruff check src/
	@echo "→ Linting Layer 3..."
	cd value-fabric/layer3-knowledge && ruff check src/
	@echo "→ Linting Layer 4..."
	cd value-fabric/layer4-agents && ruff check src/
	@echo "→ Linting Layer 5..."
	cd value-fabric/layer5-ground-truth && ruff check src/
	@echo "→ Linting Layer 6..."
	cd value-fabric/layer6-benchmarks && ruff check src/

typecheck: ## Type-check all Python layers with mypy
	@echo "→ Type-checking Layer 1..."
	cd value-fabric/layer1-ingestion && mypy src/ --ignore-missing-imports
	@echo "→ Type-checking Layer 2..."
	cd value-fabric/layer2-extraction && mypy src/ --ignore-missing-imports
	@echo "→ Type-checking Layer 3..."
	cd value-fabric/layer3-knowledge && mypy src/ --ignore-missing-imports
	@echo "→ Type-checking Layer 4..."
	cd value-fabric/layer4-agents && mypy src/ --ignore-missing-imports
	@echo "→ Type-checking Layer 5..."
	cd value-fabric/layer5-ground-truth && mypy src/ --ignore-missing-imports

# ─── Testing ──────────────────────────────────────────────────────────────────

test: test-layer1 test-layer2 test-layer3 test-layer4 ## Run all backend unit tests

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

test-frontend: ## Run frontend unit tests
	cd frontend && pnpm run test

test-e2e: ## Run Playwright end-to-end tests (requires running stack)
	cd frontend && pnpm exec playwright test

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

# ─── Cleanup ─────────────────────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅  Clean complete"
