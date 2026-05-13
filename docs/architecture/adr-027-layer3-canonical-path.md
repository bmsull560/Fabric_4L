# ADR-027: Layer 3 Canonical Runtime Path

## Status

Accepted — 2026-05-13

Supersedes: ADR-027-draft (Proposed, 2026-05-12)

## Unified Direction

**Service-first canonical path model.** The `services/` tree contains actual implementations; `value_fabric/` serves as a thin namespace shim for backward compatibility only. This eliminates the dual-path ambiguity that caused the ADR-027 incident and aligns all layers with the proven Layer 4/5 pattern.

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

**Long-term (Accepted):**

- **Adopt service-first canonical paths for all layers.** `services/layer*-*/src/` is the authoritative implementation tree.
- **`value_fabric/layerX/` becomes a thin namespace shim only** — no implementation logic, only `__init__.py` path appending for backward compatibility.
- **Migrate Layer 1 first** (already partially migrated; use as pilot)
- **Layers 2, 3, 6 follow** in priority order by incident history
- **Layer 4 is already compliant** — use as the template

**Migration Strategy:**

1. For each layer, move implementation logic from `value_fabric/layerX/` to `services/layerX-*/src/`
2. Replace `value_fabric/layerX/` files with thin `__init__.py` shims that append the service source path
3. Update cross-layer imports to use service packages directly (or keep namespace imports during transition)
4. Run contract tests (`tests/arch/test_canonical_module_sentinels.py`, `tests/contract/test_import_topology.py`) after each layer
5. Remove shim appending from `value_fabric/__init__.py` once all consumers have migrated

**Rollback Plan:**
If a layer migration fails, revert only that layer's `value_fabric/layerX/__init__.py` to restore path appending for the affected service. Do not roll back the entire decision.

## Options Considered

### Option A: Service-first canonical paths (selected)

**Pros:**

- Eliminates the dual-path ambiguity that caused the ADR-027 deletion incident
- Aligns all layers with the proven Layer 4/5 pattern
- Reduces cognitive load: "the implementation lives in the service directory, period"
- Enables each service to be self-contained and independently deployable
- `value_fabric/` namespace can be deprecated incrementally without breaking consumers

**Cons:**

- Requires staged migration across layers (not a single-PR change)
- Cross-layer imports must be updated layer-by-layer
- Tests and CI scripts need temporary dual-path awareness during transition

### Option B: Keep `value_fabric/layer3/` as canonical (rejected)

**Reason for rejection:** Perpetuates the root cause. The `value_fabric/` directory is vulnerable to broad operations and accidental deletion, and the wrapper indirection provides no value.

### Option C: Keep both paths with bidirectional compatibility (rejected)

**Reason for rejection:** Creates permanent technical debt. We accept temporary dual-path awareness during migration, but the end state must be unambiguous.

## Consequences

- **`services/layer*-*/src/` is the runtime source of truth** for all layers
- **`value_fabric/layerX/` is a backward-compatibility shim only** — no new implementation logic may be added
- **Cross-layer imports should migrate** from `value_fabric.layerX.*` to direct service package imports where possible
- **CI contract tests enforce shim discipline:** `tests/arch/test_canonical_module_sentinels.py` verifies compatibility modules contain only re-exports
- **Future migration checklist per layer:**

  - Inventory all `value_fabric.layerX` imports across the codebase
  - Move implementation files to `services/layerX-*/src/`
  - Replace `value_fabric/layerX/` with thin `__init__.py` path appender
  - Staged PR with contract tests passing
  - Remove service path from `value_fabric/__init__.py` once layer is fully migrated

## Migration Status

| Layer | Status | Service Path | Notes |
| :---- | :----- | :----------- | :---- |
| 1 | In Progress | `services/layer1-ingestion/src/` | Already partially migrated; `skills/` package added directly in service |
| 2 | Pending | `services/layer2-extraction/src/` | Awaiting Layer 1 pilot completion |
| 3 | Pending | `services/layer3-knowledge/src/` | Incident layer; high priority |
| 4 | Compliant | `services/layer4-agents/src/` | Template for other layers |
| 5 | Compliant | `services/layer5-ground-truth/src/` | Template for other layers |
| 6 | Pending | `services/layer6-benchmarks/src/` | Low incident history; lowest priority |

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
