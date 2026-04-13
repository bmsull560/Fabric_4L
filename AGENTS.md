# AGENTS.md — Contributor Guide for AI Agents and Developers

This file explains how to work safely and effectively in the Value Fabric repository,
whether you are a human developer or an AI coding agent. Read this before making changes.

---

## Repository structure at a glance

```
value-fabric/
  layer1-ingestion/    # Data ingestion — Playwright, Redis, PostgreSQL
  layer2-extraction/   # Ontology-guided extraction — LLM + RDF/OWL
  layer3-knowledge/    # Knowledge graph API — Neo4j + pgvector
  layer4-agents/       # Agentic engine — LangGraph orchestration, REST API
  layer5-ground-truth/ # Ground-truth store + evaluation API
  layer6-benchmarks/   # Benchmark harness
  shared/
    identity/          # Cross-layer auth — JWT, API keys, RBAC, middleware
    audit/             # Append-only audit log (DB trigger-enforced)

layer4-agents/         # Agent behavior artifacts (prompts, skills, workflows)
  agents/              # Agent definitions (Markdown frontmatter + prose)
  skills/              # Atomic skill definitions (tool schemas + behavior)
  workflows/           # Multi-step workflow definitions

contracts/             # Source of truth for all interfaces
  tool-manifests/      # JSON Schema for every agent tool/skill
  openapi/             # Generated OpenAPI specs per layer (do not hand-edit)
  jsonschema/          # Shared data model schemas

frontend/              # React + TypeScript UI (Vite)
k8s/                   # Kubernetes manifests
monitoring/            # Prometheus + Grafana
packs/                 # Domain vertical extensions
docs/                  # Architecture docs and runbooks
tests/                 # Cross-layer integration and agent evals
```

---

## Change safety rules

These rules exist because this is a production multi-agent system where behavior
emerges from interactions between agents, tools, and the knowledge graph.

### P0 — Never do these

1. **Do not commit secrets.** No API keys, passwords, or tokens in any file. Use `.env` (gitignored).
2. **Do not modify `value-fabric/shared/identity/` without a security review.** This is the
   cross-layer authentication and authorization library. Bugs here affect every service.
3. **Do not modify `value-fabric/layer4-agents/migrations/` by hand.** Use Alembic to generate
   new migration files: `alembic revision --autogenerate -m "description"`.
4. **Do not change a tool manifest in `contracts/tool-manifests/` without updating the
   corresponding skill definition in `layer4-agents/skills/`.** Contracts and skills must stay in sync.
5. **Do not remove or weaken existing tests.** If a test is blocking you, understand why before
   touching it. Tests encode behavioral contracts.

### P1 — Be careful with these

- **Provider changes** (`value-fabric/layer*/src/`) — These affect live data flows. Changing
  extraction logic can alter the shape of the knowledge graph, breaking downstream agents.
- **Ontology changes** (`packs/*/ontology.json`) — Entity type and relationship changes are
  effectively schema migrations for the knowledge graph.
- **Agent/skill definitions** (`layer4-agents/agents/`, `layer4-agents/skills/`) — Prompt changes
  alter agent behavior. Always add or update evals in `tests/evals/` when changing prompts.

---

## Required verification steps

Before opening a PR, run:

```bash
make verify
```

This runs: lint → type-check → unit tests → contract tests → build.

For agent/skill changes, also run:

```bash
make evals
```

This runs the golden-trace evaluation suite in `tests/evals/`.

Individual layer commands:

```bash
make test-layer1    # Layer 1 unit + integration tests
make test-layer2    # Layer 2 unit + integration tests
make test-layer3    # Layer 3 unit + integration tests
make test-layer4    # Layer 4 unit + integration tests
make test-frontend  # Frontend unit + type-check
```

---

## How to add a new agent skill

1. Create a skill definition in `layer4-agents/skills/<name>.md`:
   ```markdown
   ---
   name: my-skill
   description: What this skill does
   ---
   # My Skill
   ## Parameters
   - `param1`: Type and description (required)
   ## Steps
   1. Step one
   ## Output
   What is returned
   ```

2. Create the corresponding tool manifest in `contracts/tool-manifests/<name>.json`:
   ```json
   {
     "$schema": "https://json-schema.org/draft/2020-12/schema",
     "name": "my_skill",
     "description": "What this skill does",
     "parameters": {
       "type": "object",
       "properties": {
         "param1": { "type": "string", "description": "..." }
       },
       "required": ["param1"]
     }
   }
   ```

3. Implement the tool function in `value-fabric/layer4-agents/src/tools/`.

4. Register the tool in `value-fabric/layer4-agents/src/tools/__init__.py`.

5. Add a golden-trace eval in `tests/evals/skills/test_<name>.py`.

6. Run `make verify && make evals`.

---

## How to add a new agent

1. Create the agent definition in `layer4-agents/agents/<name>_agent.md` with frontmatter
   listing its allowed skills.
2. Implement the agent in `value-fabric/layer4-agents/src/agents/<name>.py`.
3. Register it in the agent router.
4. Add integration tests in `value-fabric/layer4-agents/tests/`.
5. Document its purpose and constraints in the definition file.

---

## How to add a new provider

1. Create the provider adapter in the relevant layer's `src/` directory.
2. Accept configuration via environment variables only — never hardcode credentials.
3. Add the new env vars to `value-fabric/.env.example` with placeholder values.
4. Document the provider in `Providers.md`.
5. Write integration tests that can run without the real provider (use mocks/fixtures).

---

## Debugging with traces

Layer 4 emits OpenTelemetry traces for every agent run and tool call.

To inspect traces locally:
```bash
docker compose up -d jaeger
# Open http://localhost:16686
```

To correlate a failed agent run:
1. Find the `trace_id` in the response or agent log output.
2. Search for it in Jaeger or your observability backend.
3. Inspect the tool call sequence and intermediate outputs.

For production traces, see `monitoring/` for Grafana dashboards.

---

## Coding standards

- **Python**: Follow `ruff` rules (configured in each layer's `pyproject.toml`). Type hints required.
- **TypeScript**: Follow ESLint config in `frontend/`. No `any` unless unavoidable.
- **Tests**: Deterministic unit tests only — no external calls. Use `pytest-mock` or `unittest.mock`.
- **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`, `test:`.
- **Secrets**: Use `value-fabric/.env.example` for templates. Never put real values anywhere tracked by git.
