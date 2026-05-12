# ADR-027: Layer 3 Canonical Runtime Path

## Status

Proposed

## Context

On 2026-05-12, commit `d71ca0c1` ("feat(anti-drift,layer2,makefile)") accidentally deleted 124 tracked files under `value_fabric/layer3/`. This broke all service-layer wrappers in `services/layer3-knowledge/src/` that import from `value_fabric.layer3.*`, causing `ModuleNotFoundError` at startup.

The incident revealed that Layer 3 has a **dual-path structure** that creates runtime fragility:

- **Canonical runtime**: `value_fabric/layer3/` (api, schema, migrations, services, agents, analytics, tracing, retrieval, etc.)
- **Service wrappers**: `services/layer3-knowledge/src/api/` and `src/migrations/` contain import-only wrappers that re-export from `value_fabric.layer3.*`

Both paths are actively used:

- `value_fabric.layer3.api.routes.entities` is imported by tests and other layers
- `services.layer3_knowledge.src.api.routes.entities` is a wrapper: `from value_fabric.layer3.api.routes.entities import *`

This indirection provides no value and creates a single point of failure: if `value_fabric/layer3/` is deleted, the entire Layer 3 API surface fails at import time.

## Decision

**Short-term (P0 recovery, done):**

- Restored `value_fabric/layer3/` from `HEAD~2` (commit before accidental deletion)
- Fixed test-drift and field-name mismatches uncovered by the restoration
- All 13 Layer 3 tests now pass

**Long-term:**

- **Keep `value_fabric/layer3/` as the canonical runtime implementation** for now
- **Do not consolidate paths in the same PR** as the P0 recovery
- Track a future migration to eliminate the wrapper layer under `services/layer3-knowledge/src/api/`

## Options Considered

### Option A: Keep `value_fabric/layer3/` as canonical (selected)

**Pros:**

- Already established as the runtime source of truth per `AGENTS.md` canonical paths
- Cross-layer imports from Layer 2, Layer 4, Layer 5 depend on `value_fabric.layer3.*`
- Minimal disruption to current architecture
- Tests, OpenAPI exports, and Docker entrypoints already reference this path

**Cons:**

- Duplicate wrapper layer in `services/layer3-knowledge/src/api/` adds confusion
- Risk of future accidental deletion if broad operations touch `value_fabric/`

### Option B: Migrate canonical implementation into `services/layer3-knowledge/src/`

**Pros:**

- Eliminates the wrapper indirection layer
- Aligns with the deployable service pattern used by Layers 1, 2, 5, 6

**Cons:**

- Massive cross-layer impact: every `from value_fabric.layer3 import ...` across the codebase must be rewritten
- Breaks `AGENTS.md` canonical path governance until all references are updated
- Requires simultaneous changes to tests, OpenAPI scripts, Docker entrypoints, CI workflows, and docs
- High risk of introducing new drift during migration

### Option C: Keep both paths with bidirectional compatibility

**Pros:**

- Maximum compatibility during transition

**Cons:**

- Creates permanent technical debt
- Increases maintenance burden
- Still vulnerable to accidental deletion of either path

## Consequences

- **value_fabric/layer3/ remains the runtime source of truth**
- **services/layer3-knowledge/src/api/ wrappers are tolerated** as a service-local indirection layer
- **Future migration to Option B** should be planned as a dedicated project with:

  - Complete inventory of all `value_fabric.layer3` imports across layers
  - Staged PRs per consumer layer
  - Contract tests to verify no API behavior changes
  - ADR ratification before implementation

## Incident Root Cause

Commit `d71ca0c1` performed broad file operations (likely `git rm` or similar) that deleted `value_fabric/layer3/` files without corresponding changes to the service wrappers or any migration path. The commit was focused on Layer 2 anti-drift hardening and Makefile changes; Layer 3 deletion was accidental.

## Prevention Measures

1. **CI gate**: Add a check that `value_fabric/layer3/` files exist and import cleanly
2. **Contract test**: Verify `services.layer3_knowledge.src.api.*` modules import without `ModuleNotFoundError`
3. **Code review**: Flag any commit that removes >20 files from a canonical path without an explicit deprecation ADR
4. **Wrapper audit**: Schedule removal of import-only wrapper files in `services/layer3-knowledge/src/api/`

## Related

- `AGENTS.md` canonical paths policy
- `canonical-paths-policy.md`
- `reports/MIGRATION_HARDENING_REPORT_2026-05-12.md`
