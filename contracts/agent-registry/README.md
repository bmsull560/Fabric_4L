# Agent Registry Contracts

This directory is the **semantic source of truth** for Layer 4 agent behavior. Phase 1 established the registry without changing runtime behavior; **Phase 2** adds a compatibility matrix consumed by runtime, AG-UI, lint, and CI validation in warning mode. The registry records the minimum contract metadata needed to detect architectural drift in agents, prompts, reasoning policies, tools, workflows, memory references, and semantic event envelopes.

## Directory Structure

| Path | Purpose |
|---|---|
| `schemas/` | JSON Schema contracts for registry documents. |
| `agents/manifest.json` | Canonical production Layer 4 agent roster and expected decision envelopes. |
| `compatibility-matrix.json` | Phase 2 semantic-contract compatibility matrix covering agent, prompt, tool, workflow, memory, and AG-UI event envelope versions. |
| `tools/manifest.json` | Centralized tool interface registry mapped to `contracts/tool-manifests/*.json`. |
| `prompts/` | Versioned prompt metadata and changelog evidence. |
| `reasoning-policies/` | Confidence, evidence, escalation, and allowed-tool policy contracts. |
| `workflows/` | Workflow state-machine entries with states, transitions, and invariants. |

The compatibility matrix intentionally starts with `enforcement_default: "warn"`. Runtime validators and frontend event schemas surface semantic-contract gaps without blocking execution until strict enforcement is explicitly promoted through the governance process.

## Layer 4 Runtime Model Selectors

Layer 4 runtime selectors must remain aligned with contract-governed model inventory. Current selectors approved for runtime defaults and fallback:

- `gpt-4`
- `gpt-4o`
- `claude-3-sonnet-20240229`

## Change Discipline

Registry changes are governed by `contracts/GOVERNANCE.md`. Prompt,
reasoning-policy, workflow, and tool-interface changes must carry
changelog or migration notes and remain compatible with the existing
Contract Council RFC process. CI validation initially runs in
warning mode so teams can close coverage gaps before enforcement is
promoted to blocking.

## Validation

Run the registry contract validator from the repository root. The same command validates the Phase 2 `compatibility-matrix.json` and emits warnings when registered agents and compatibility entries drift:

```bash
python scripts/ci/check_agent_registry.py
```

Use strict mode when preparing promotion from warning-only coverage checks to
blocking enforcement:

```bash
python scripts/ci/check_agent_registry.py --strict
```
