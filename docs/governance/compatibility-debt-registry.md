# Compatibility Debt Registry

This registry tracks **runtime** compatibility wrappers/shims that exist to preserve backward compatibility while canonical paths are adopted.

## Policy

- New runtime `legacy`/`compatibility` markers require a matching tracker entry here before merge.
- Each entry must include owner, reason, and an explicit target removal date.
- Entries are reviewed monthly and pruned when removed from runtime.

## Review Cadence

- **Last reviewed:** 2026-05-12 (updated for Layer 3 shim-only inventory and exception audit)
- **Next review due:** 2026-06-12
- **Review owner:** Platform Architecture

## Registry

| ID | Runtime path | Type | Owner | Reason | Target removal date |
|---|---|---|---|---|---|
| COMPAT-L1-001 | `value_fabric/layer1/api/routes/compatibility.py` | Route wrapper | layer1-ingestion | Maintains legacy ingestion route aliases while clients move to canonical route modules. | 2026-08-31 |
| COMPAT-L3-001 | `value_fabric/layer3/api/routes/compat_aliases.py` | Route wrapper | layer3-knowledge | Keeps compatibility aliases for route naming transitions in Layer 3 APIs. | 2026-08-31 |
| COMPAT-L3-002 | `value_fabric/layer3/api/routes/entity_compat.py` | Route shim | layer3-knowledge | Supports older entity endpoint patterns while frontend and SDK consumers migrate. | 2026-08-31 |
| COMPAT-L3-003 | `services/layer3-knowledge/src/` (mirrored dirs only) | Package shim tree | layer3-knowledge + Platform Architecture | Compatibility re-export tree for mirrored runtime modules; canonical implementation now lives in `value_fabric/layer3` and is enforced by `scripts/ci/check_layer3_source_mirror.py`. Service-local exceptions (`api/`, `agents/`, `cache/`, `docs/`, `metrics/`, top-level `config.py`, migrations) are intentionally non-shim and tracked in `docs/governance/layer3-service-source-inventory.md` with removal/migration target. | 2026-09-30 |
| COMPAT-L5-001 | `value_fabric/layer5/` | Package shim tree | layer5-ground-truth | Compatibility re-export tree that delegates to canonical `services/layer5-ground-truth/src/layer5_ground_truth`. | 2026-09-30 |
| COMPAT-WEB-001 | `apps/web/src/api/legacy.ts` | Frontend API shim | web-platform | Legacy web API adapter maintained during phased migration to canonical API clients. | 2026-07-31 |
| COMPAT-L4-001 | `services/layer4-agents/src/api/routes/frontend_compat.py` | Route shim | layer4-agents | Preserves historical frontend contract during workflow API consolidation. | 2026-08-31 |
| COMPAT-SDK-001 | `sdk/python/src/valuefabric/cli/workflows.py` | CLI compatibility surface | sdk | Backward-compatible CLI workflow commands pending full canonical command migration. | 2026-09-30 |

## Monthly Prune Procedure

1. Run `pytest tests/ci/test_compatibility_debt_registry.py`.
2. For each listed path, confirm whether the shim/wrapper still exists and is still required.
3. Remove entries that are no longer present in runtime code.
4. Update `Last reviewed` and `Next review due` dates.
5. If any target date has passed, either remove the shim or add a dated extension note in this file.

## Layer 3 Source Ownership and Exceptions

- **Canonical owner/path:** `value_fabric/layer3` (Layer 3 runtime implementation).
- **Compatibility owner/path:** `services/layer3-knowledge/src` for designated mirrored directories only.
- **Allowed non-mirrored exceptions in service tree:** `api/`, `agents/`, `cache/`, `docs/`, `metrics/`, and top-level `config.py` stay service-local and are not required to exist under `value_fabric/layer3`.
- **Guardrail:** mirrored paths in `services/layer3-knowledge/src` must remain thin `from value_fabric.layer3... import *` shims; implementation logic must not diverge from canonical runtime modules.
