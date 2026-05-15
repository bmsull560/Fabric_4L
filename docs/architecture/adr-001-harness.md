# ADR-001: Fabric Harness as the Governed Execution Spine for Agentic Value Workflows

## Status
Accepted

## Context
Fabric_4L has distinct layers (L1-L6) that handle specific concerns: ingestion, extraction, knowledge, agents, ground truth, and benchmarks. The challenge is coordinating these layers into governed, auditable value-execution workflows without creating a competing framework.

## Decision
Fabric_4L will implement a cross-layer **harness** in L4 that coordinates agent workflows, tool execution, checkpointing, validation, approval, and telemetry for value-modeling workflows.

## Consequences

- **L4 remains the orchestration layer.** The harness lives in `services/layer4-agents/src/harness/`.
- **L5 remains the ground-truth and validation layer.** The harness provides a hook interface to L5, not a replacement.
- **L3 remains the knowledge and context layer.** The harness resolves context from L3, doesn't duplicate it.
- **L6 remains the benchmark and policy layer.** Benchmark references are passed through, not interpreted.
- The harness does not replace these layers.
- The harness governs how they interact.
- Customer-facing outputs require validation or approved override.

## Architecture

```
L4 Agents (harness)
  ├── HarnessRun lifecycle
  ├── StateMachine (deterministic transitions)
  ├── ToolContractRegistry (governed tool invocations)
  ├── HumanGateManager (approval gates)
  ├── CheckpointManager (deterministic snapshots)
  ├── ValidationHook (L5 integration interface)
  ├── TelemetryEmitter (structured trace events)
  └── PublicationPolicies (customer-facing output control)
```

## Invariants

1. Every HarnessRun has `tenant_id`.
2. Every HarnessRun has `trace_id`.
3. Every state transition is validated against the transition map.
4. Terminal runs (DONE, FAILED, CANCELLED) cannot transition.
5. Every checkpoint is tied to `run_id` and `tenant_id` with deterministic hashing.
6. Same payload always produces the same checkpoint hash.
7. Every high-risk tool action requires an approval policy.
8. Every customer-facing output requires L5 validation or explicit human override.
9. Failed validation blocks publication unless override policy explicitly allows.
10. Unavailable L5 validation routes to `needs_review` or `insufficient_evidence` — never silently approves.
11. Every telemetry event includes `trace_id` and `tenant_id`.
12. Tenant isolation is enforced at all service boundaries.
13. Cross-tenant access returns 404 (or equivalent error).
14. Invalid state transitions return deterministic validation errors.
15. The harness must not duplicate L3, L5, or L6 responsibilities.
16. The harness must not create a second tenant-context mechanism.
17. The harness must degrade gracefully when optional downstream services are unavailable.

## Non-Decisions (Out of Scope)

- Full self-improvement automation (loop 7 from the blueprint)
- Automated prompt optimization
- Reinforcement learning-based routing
- Complex rollback orchestration for every tool
- Multi-zone deployment model
- Full procedural memory system
- SQL persistence (in-memory MVP; upgrade path documented)
- FastAPI routes (deferred; test patterns established)
- Frontend changes (deferred until backend validated)

## Implementation Notes

- Uses Pydantic v2 for all models.
- In-memory storage for MVP.
- Deterministic SHA-256 hashing for checkpoints.
- Explicit error types for all failure modes.
- Structured trace events (no free-text-only logs).
- Test coverage for all state transitions, policies, and invariants.
