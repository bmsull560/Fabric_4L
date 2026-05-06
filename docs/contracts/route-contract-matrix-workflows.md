# Route-Contract Matrix: Workflow Hooks vs Agents Router

## Canonical naming

- **Canonical backend noun: `run`** (`AgentRun` in `services/api/app/models/schemas.py`).
- **Compatibility/frontend noun: `workflow`** (used by `apps/web/src/hooks/useWorkflows.ts`).
- `services/api/app/routers/agents.py` now exposes both `/agents/runs*` (canonical) and `/agents/workflows*` (compatibility) with payload adapters.

## Source of truth for frontend contract tests

Frontend contract tests consume a single OpenAPI source for Layer 4:

- `contracts/openapi/layer4-agents.json`

Resolved in test runtime via:

- `apps/web/src/api/__tests__/contract/openapi-validator.ts`

## Matrix

| Frontend call (`useWorkflows.ts`) | Expected behavior | Router endpoint | Canonical mapping |
|---|---|---|---|
| `POST /workflows` | Create workflow and return workflow id fields | `POST /agents/workflows` | delegates to `POST /agents/runs` |
| `GET /workflows/active` | List active workflows for polling | `GET /agents/workflows/active` | read from `db.agent_runs.list(...)` |
| `GET /workflows/{id}` | Fetch workflow detail/status | `GET /agents/workflows/{id}` | mirrors `GET /agents/runs/{run_id}` |
| `DELETE /workflows/{id}` | Cancel workflow | `DELETE /agents/workflows/{id}` | delegates to `POST /agents/runs/{run_id}/cancel` |
| `POST /workflows/{id}/pause` | Pause running workflow | `POST /agents/workflows/{id}/pause` | status update on `AgentRun` |
| `POST /workflows/{id}/resume` | Resume paused workflow | `POST /agents/workflows/{id}/resume` | delegates to `POST /agents/runs/{run_id}/resume` |
| `GET /workflows/{id}/events` | SSE status stream | `GET /agents/workflows/{id}/events` | emits workflow-shaped event envelope |

