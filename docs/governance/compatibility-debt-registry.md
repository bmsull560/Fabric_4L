# Compatibility Debt Registry

This registry tracks **runtime** compatibility wrappers/shims that exist to preserve backward compatibility while canonical paths are adopted.

## Policy

- New runtime `legacy`/`compatibility` markers require a matching tracker entry here before merge.
- Launch freeze policy: no net-new runtime compatibility wrapper/shim file under canonical runtime roots may merge without explicit Platform Architecture approval recorded here.
- Each entry must include owner, reason, an explicit target removal date, review metadata, and a post-launch removal ticket.
- Entries are reviewed monthly and pruned when removed from runtime.

## Review Cadence

- **Last reviewed:** 2026-05-12 (updated for Layer 3 shim-only inventory, shim conflict cleanup, and exception audit)
- **Next review due:** 2026-06-12
- **Review owner:** Platform Architecture

## Registry

| ID | Runtime path | Type | Owner | Reason | Target removal date | Review metadata | Post-launch removal ticket |
|---|---|---|---|---|---|---|---|
| COMPAT-L1-001 | `services/layer1-ingestion/src/api/routes/compatibility.py` | Route wrapper | layer1-ingestion | Maintains legacy ingestion route aliases while clients move to canonical route modules. | 2026-08-31 | Platform Architecture approved 2026-05-12; reviewed 2026-05-12. | PLATARCH-REMOVE-L1-001 |
| COMPAT-L3-001 | `value_fabric/layer3/api/routes/compat_aliases.py` | Route wrapper | layer3-knowledge | Keeps compatibility aliases for route naming transitions in Layer 3 APIs. | 2026-08-31 | Platform Architecture approved 2026-05-12; reviewed 2026-05-12. | PLATARCH-REMOVE-L3-001 |
| COMPAT-L3-002 | `value_fabric/layer3/api/routes/entity_compat.py` | Route shim | layer3-knowledge | Supports older entity endpoint patterns while frontend and SDK consumers migrate. | 2026-08-31 | Platform Architecture approved 2026-05-12; reviewed 2026-05-12. | PLATARCH-REMOVE-L3-002 |
| COMPAT-L3-003 | `services/layer3-knowledge/src/` | Package shim tree | layer3-knowledge | Compatibility re-export tree for mirrored runtime modules; canonical implementation now lives in `value_fabric/layer3` and is enforced by `scripts/ci/check_layer3_source_mirror.py`. Service-local exceptions (`api/`, `agents/`, `cache/`, `docs/`, `metrics/`, top-level `config.py`, migrations) are intentionally non-shim and tracked in `docs/governance/layer3-service-source-inventory.md` with owner/date reaffirmed in the 2026-05-12 inventory sweep. | 2026-10-31 | Platform Architecture approved 2026-05-12; reviewed 2026-05-12. | PLATARCH-REMOVE-L3-003 |
| COMPAT-L3-004 | `value_fabric/layer3/api/compat_wiring.py` | Version compatibility wiring | layer3-knowledge | Preserves request and response transformation wiring while legacy v1 clients complete removal. | 2026-08-31 | Platform Architecture approved 2026-05-12; reviewed 2026-05-12. | PLATARCH-REMOVE-L3-004 |
| COMPAT-L3-005 | `value_fabric/layer3/services/compat_metrics.py` | Compatibility metrics surface | layer3-knowledge | Tracks deprecated Layer 3 route and field usage until the remaining compatibility paths are removed. | 2026-08-31 | Platform Architecture approved 2026-05-12; reviewed 2026-05-12. | PLATARCH-REMOVE-L3-005 |
| COMPAT-L5-001 | `value_fabric/layer5/` | Package shim tree | layer5-ground-truth | Compatibility re-export tree that delegates to canonical `services/layer5-ground-truth/src/layer5_ground_truth`. | 2026-09-30 | Platform Architecture approved 2026-05-12; reviewed 2026-05-12. | PLATARCH-REMOVE-L5-001 |
| COMPAT-WEB-001 | `apps/web/src/api/legacy.ts` | Frontend API shim | web-platform | Legacy web API adapter maintained during phased migration to canonical API clients. | 2026-07-31 | Platform Architecture approved 2026-05-12; reviewed 2026-05-12. | PLATARCH-REMOVE-WEB-001 |
| COMPAT-L4-001 | `services/layer4-agents/src/api/routes/frontend_compat.py` | Route shim | layer4-agents | Preserves historical frontend contract during workflow API consolidation. | 2026-08-31 | Platform Architecture approved 2026-05-12; reviewed 2026-05-12. | PLATARCH-REMOVE-L4-001 |
| COMPAT-SDK-001 | `sdk/python/src/valuefabric/cli/workflows.py` | CLI compatibility surface | sdk | Backward-compatible CLI workflow commands pending full canonical command migration. | 2026-09-30 | Platform Architecture approved 2026-05-12; reviewed 2026-05-12. | PLATARCH-REMOVE-SDK-001 |

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
