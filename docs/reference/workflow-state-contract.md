# Platform Workflow State Contract

## Purpose

This contract defines the canonical workflow/job lifecycle across Value Fabric layers (L1–L6), including transition rules, retry semantics, terminal failure handling, and correlation IDs.

## Canonical States

| Canonical state | Description | Terminal |
|---|---|---|
| `created` | Request accepted, execution not yet queued. | No |
| `queued` | Queued for worker/agent execution. | No |
| `running` | Active processing in progress. | No |
| `waiting_dependency` | Blocked on upstream/downstream prerequisite state. | No |
| `retrying` | Prior attempt failed with retryable error; next attempt scheduled/in progress. | No |
| `paused` | Explicitly paused by operator/system gate. | No |
| `cancelled` | Explicitly cancelled; no further transitions allowed. | Yes |
| `succeeded` | Completed successfully; side effects committed. | Yes |
| `failed_terminal` | Failed with terminal/non-retryable error or retry budget exhausted. | Yes |

## Transition Rules

Allowed transitions:

- `created -> queued | running | cancelled`
- `queued -> running | retrying | cancelled | failed_terminal`
- `running -> waiting_dependency | retrying | paused | succeeded | failed_terminal | cancelled`
- `waiting_dependency -> queued | running | retrying | cancelled | failed_terminal`
- `retrying -> queued | running | failed_terminal | cancelled`
- `paused -> queued | running | cancelled`

Forbidden transitions:

- Any transition *out of* terminal states: `cancelled`, `succeeded`, `failed_terminal`.
- `succeeded -> *`
- `failed_terminal -> *`
- `cancelled -> *`

## Retry Semantics

- Retryable errors MUST set `state=retrying` with structured metadata:
  - `retry.attempt` (1-indexed)
  - `retry.max_attempts`
  - `retry.next_retry_at` (RFC3339 UTC)
  - `retry.reason_code`
- A retry MAY resume into `queued` (deferred) or `running` (immediate local retry).
- When `retry.attempt > retry.max_attempts`, transition to `failed_terminal`.
- Non-retryable errors MUST transition directly to `failed_terminal`.

## Terminal Error Contract

On terminal failure, responses/events MUST include:

- `error.code` (stable machine code)
- `error.message` (human-readable)
- `error.retryable=false`
- `error.layer` (`layer1` … `layer6`)
- `error.occurred_at` (RFC3339 UTC)
- Optional: `error.caused_by_state`, `error.upstream_job_id`

## Correlation and Identity IDs

Every workflow/job payload and event MUST include:

- `correlation_id`: End-to-end request lineage ID across layers.
- `trace_id`: Distributed tracing ID (OpenTelemetry compatible).
- `workflow_id`: Layer 4 workflow execution ID when orchestration is involved.
- `job_id`: Layer-local execution ID.

Cross-layer dependency IDs (when applicable):

- `content_id` (L1 canonical content object)
- `extraction_job_id` (L2 extraction execution)
- `graph_sync_status` (`pending` | `syncing` | `succeeded` | `failed`)
- `truth_approval_status` (`pending` | `approved` | `rejected`)

## Layer Endpoint → State Mapping

### Layer 1 (ingestion)

| Endpoint pattern | Initial state | Sync/Async transition model |
|---|---|---|
| `POST /v1/content` | `created` | Synchronous request acknowledgement to `queued`; async processing to `running/succeeded/failed_terminal`. |
| `GET /v1/content/{content_id}` | N/A | Read-only state projection. |

### Layer 2 (extraction)

| Endpoint pattern | Initial state | Sync/Async transition model |
|---|---|---|
| `POST /v1/extraction/jobs` | `created` | Sync acknowledgment then async `queued -> running -> succeeded/failed_terminal`. |
| `GET /v1/jobs/{extraction_job_id}` | N/A | Read-only state projection, may return any canonical state. |
| `GET /v1/jobs/{extraction_job_id}/stream` | N/A | Async event stream of state transitions and progress deltas. |

### Layer 3 (knowledge graph)

| Endpoint pattern | Initial state | Sync/Async transition model |
|---|---|---|
| `POST /v1/graph/sync` | `created` | Sync ack to `queued`; async graph write transitions (`running`, `retrying`, terminal). |
| `GET /v1/graph/sync/{job_id}` | N/A | Read-only state projection including `graph_sync_status`. |

### Layer 4 (agents/orchestration)

| Endpoint pattern | Initial state | Sync/Async transition model |
|---|---|---|
| `POST /v1/workflows` | `created` | Synchronous creation only (no execution). |
| `POST /v1/workflows/{workflow_id}/run` | `queued` | Sync execution dispatch then async orchestration (`running`, `waiting_dependency`, `retrying`, terminal). |
| `GET /v1/workflows/{workflow_id}` | N/A | Read-only state projection and dependency-state rollup. |
| `GET /v1/workflows/{workflow_id}/stream` | N/A | Async event stream of transitions, checkpoints, and dependency gate changes. |

### Layer 5 (ground truth)

| Endpoint pattern | Initial state | Sync/Async transition model |
|---|---|---|
| `POST /v1/truth/approvals` | `created` | Sync ack; async reviewer/system decision to `succeeded` (`approved`) or `failed_terminal` (`rejected/error`). |
| `GET /v1/truth/approvals/{job_id}` | N/A | Read-only state projection including `truth_approval_status`. |

### Layer 6 (benchmarks/evals)

| Endpoint pattern | Initial state | Sync/Async transition model |
|---|---|---|
| `POST /v1/benchmarks/runs` | `created` | Sync ack; async benchmark execution lifecycle. |
| `GET /v1/benchmarks/runs/{job_id}` | N/A | Read-only state projection. |

## Canonical Dependency Gating for L4

Layer 4 orchestration MUST treat these as hard dependencies before final `succeeded`:

1. `content_id` exists and is tenant-accessible.
2. `extraction_job_id` terminal `succeeded` (or explicit policy-based bypass).
3. `graph_sync_status = succeeded`.
4. `truth_approval_status = approved` for gated workflows.

If any dependency is unresolved, L4 SHOULD use `waiting_dependency` and include the blocking key in metadata.
