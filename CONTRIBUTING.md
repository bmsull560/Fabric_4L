# Contributing to Value Fabric

Thank you for your interest in contributing. Read [`AGENTS.md`](AGENTS.md) first — it covers
repo structure, change safety rules, and how to add agents, skills, and providers.

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20+ and pnpm 10+
- Docker + Docker Compose
- `make`

### Local development

```bash
# 1. Clone
git clone https://github.com/bmsull560/Fabric_4L.git && cd Fabric_4L

# 2. Configure environment
cp value-fabric/.env.example value-fabric/.env
# Edit value-fabric/.env — fill in OPENAI_API_KEY and JWT_SECRET at minimum

# 3. Start infrastructure
cd value-fabric && docker compose up -d

# 4. Install Python dependencies (per layer)
cd layer4-agents && pip install -e ".[dev]"

# 5. Install frontend dependencies
cd frontend && pnpm install

# 6. Run migrations
make migrate

# 7. Verify everything passes
make verify
```

---

## Coding standards

### Python

- Formatter and linter: **ruff** (configured in each `pyproject.toml`)
- Type checker: **mypy** — type hints required on all public functions
- Test runner: **pytest** — 80%+ coverage required on all layers
- No bare `except:` — always catch specific exception types
- Use `async/await` throughout; no blocking I/O in async contexts

### TypeScript / React

- Linter: **ESLint** (configured in `frontend/`)
- Formatter: **Prettier**
- Avoid `any` unless strictly necessary and documented
- Co-locate tests with components using Vitest

### All languages

- No secrets in code — use environment variables
- No commented-out code in PRs
- Keep functions small and focused

---

## Testing requirements

Before submitting a PR:

```bash
make verify   # lint + type-check + unit tests + contract tests
```

For agent or skill changes, also run:

```bash
make evals    # golden-trace agent evaluations
```

Test categories:

| Category | Location | Rules |
|----------|----------|-------|
| Unit | `value-fabric/*/tests/` | Deterministic, no external calls, fast |
| Integration | `value-fabric/*/tests/` | May use Docker services, marked `@pytest.mark.integration` |
| E2E | `frontend/e2e/` | Playwright, critical flows only |
| Contract | `tests/contract/` | Validate tool manifest schemas |
| Evals | `tests/evals/` | Golden traces for agent skills |

---

## Pull request process

1. Branch from `main`: `git checkout -b feat/my-feature`
2. Make focused changes — one logical change per PR
3. Ensure `make verify` passes
4. Update `CHANGELOG.md` under `## [Unreleased]`
5. Open a PR with a clear description of **what** and **why**
6. Request review from at least one maintainer

### Commit message format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(layer4): add sensitivity-analysis skill
fix(layer3): correct graph traversal depth limit
docs: update AGENTS.md with provider guide
test(layer2): add extraction golden trace
chore(deps): update ruff to 0.4.x
```

Prefixes: `feat`, `fix`, `docs`, `test`, `chore`, `refactor`, `perf`, `ci`

---

## Release process

Releases follow [Semantic Versioning](https://semver.org/):

- `MAJOR` — breaking contract or API changes
- `MINOR` — new capabilities, backward compatible
- `PATCH` — bug fixes, no behavior changes

Releases are tagged `vMAJOR.MINOR.PATCH` and documented in `CHANGELOG.md`.
