# Agent Registry Contracts

This directory is the **Phase 1 semantic source of truth** for Layer 4
agent behavior. It extends the existing `contracts/` governance model
without changing runtime behavior. The registry records the minimum
contract metadata needed to detect architectural drift in agents,
prompts, reasoning policies, tools, and workflows.

## Directory Structure

| Path | Purpose |
|---|---|
| `schemas/` | JSON Schema contracts for registry documents. |
| `agents/manifest.json` | Canonical production Layer 4 agent roster and expected decision envelopes. |
| `tools/manifest.json` | Centralized tool interface registry mapped to `contracts/tool-manifests/*.json`. |
| `prompts/` | Versioned prompt metadata and changelog evidence. |
| `reasoning-policies/` | Confidence, evidence, escalation, and allowed-tool policy contracts. |
| `workflows/` | Workflow state-machine entries with states, transitions, and invariants. |

## Change Discipline

Registry changes are governed by `contracts/GOVERNANCE.md`. Prompt,
reasoning-policy, workflow, and tool-interface changes must carry
changelog or migration notes and remain compatible with the existing
Contract Council RFC process. CI validation initially runs in
warning mode so teams can close coverage gaps before enforcement is
promoted to blocking.

## Validation

Run the registry contract validator from the repository root:

```bash
python scripts/ci/check_agent_registry.py
```

Use strict mode when preparing promotion from warning-only coverage checks to
blocking enforcement:

```bash
python scripts/ci/check_agent_registry.py --strict
```
