---
title: "Layer Runtime Path Governance Matrix"
category: "reference"
audience: "contributors"
last-reviewed: "2026-05-12"
freshness: "current"
related: ["../source-tree-canonicalization", "service-routing-and-api-version-matrix", "../../AGENTS", "../getting-started/quickstart"]
---

# Layer Runtime Path Governance Matrix

This reference is the canonical contribution guide for **where new code must be added** per platform layer.

Use this before creating files so we avoid drift into archived, compatibility-only, or wrapper-only paths.

## Policy

- **Canonical runtime paths** are the source of truth for business logic and runtime modules.
- **Legacy/compatibility paths** may remain for wiring, migration support, or compatibility imports.
- **Allowed new development target** is the only approved destination for net-new logic.
- **Deprecation owner/date** identifies who governs removal or further migration.

## Layer path matrix

| Layer | Canonical runtime paths | Legacy / compatibility paths (no net-new logic) | Allowed new development target | Deprecation owner / date |
|---|---|---|---|---|
| Layer 1 — Ingestion | `value_fabric/layer1/` | `services/layer1-ingestion/src/` (service wrapper + compatibility glue) | `value_fabric/layer1/` | Layer 1 Maintainers — target review by **2026-09-30** |
| Layer 2 — Extraction | `value_fabric/layer2/` | `services/layer2-extraction/src/` (legacy service-local module path) | `value_fabric/layer2/` | Layer 2 Maintainers — target review by **2026-09-30** |
| Layer 3 — Knowledge Graph | `value_fabric/layer3/` | `services/layer3-knowledge/src/` (deployable wrapper + compatibility imports) | `value_fabric/layer3/` | Layer 3 Maintainers — target review by **2026-09-30** |
| Layer 4 — Agents | `value_fabric/layer4/` (canonical runtime namespace; resolves into `services/layer4-agents/src/`) | `layer4_agents/` (deprecated compatibility shim), `services/layer4-agents/src/` (deployable source tree) | `value_fabric/layer4/` | Layer 4 Maintainers — `layer4_agents/` deprecation started **2026-05-12**, removal review by **2026-09-30** |
| Layer 5 — Ground Truth | `services/layer5-ground-truth/src/layer5_ground_truth/` | `value_fabric/layer5/` (compatibility shims only) | `services/layer5-ground-truth/src/layer5_ground_truth/` | Layer 5 Maintainers — shim removal target review by **2026-09-30** |
| Layer 6 — Benchmarks | `value_fabric/layer6/` | `services/layer6-benchmarks/src/` (service wiring + compatibility wrappers only) | `value_fabric/layer6/` | Layer 6 Maintainers — target review by **2026-09-30** |

Layer 6 note: when compatibility wrappers are present under `services/layer6-benchmarks/src/`, they are wrapper-only and cannot contain local domain logic; CI enforces this via `scripts/ci/check_layer6_wrapper_drift.py`, and `scripts/check_mirrored_files.py` enforces byte-alignment against the manifest-declared wrapper template in `scripts/mirrored_files.json`.


## Cross-root import policy (allowed vs forbidden)

### Allowed imports in production/runtime code

- Runtime-to-runtime imports within canonical roots (for example `value_fabric/layerX/*`, `value_fabric/shared/*`, and `services/layer5-ground-truth/src/layer5_ground_truth/*`).
- Compatibility imports that remain inside approved compatibility wrappers documented in this matrix.

### Forbidden imports in production/runtime code

- Any import from `prototypes/`.
- Any import from `docs/archive/`.
- Any import from other non-runtime roots that are not canonical runtime or approved compatibility wrapper paths.

These restrictions are enforced by architecture tests (`tests/arch/test_no_non_runtime_imports.py`) and frontend hygiene linting (`apps/web/scripts/quality/assert-frontend-hygiene.mjs`).

## Contributor checklist (required)

Before opening a PR with backend runtime changes:

1. Confirm the target layer in this matrix.
2. Add net-new logic only to the canonical runtime path.
3. Keep service wrapper changes minimal and wiring-only.
4. If compatibility code is touched, add a TODO with migration intent and owner.

## Layer 3 settings module ownership

- **Canonical settings module:** `value_fabric/layer3/config/settings.py`.
- **Compatibility-only shim:** `value_fabric/layer3/config.py` (must only re-export `Settings` and `get_settings`).
- **CI drift guardrail:** `scripts/ci/check_layer3_settings_shim_drift.py` via `.github/workflows/layer3-wrapper-drift.yml`.

## Layer 3 app_monolith ownership note

- Canonical implementation: `value_fabric/layer3/api/app_monolith.py`.
- Compatibility shim only: `services/layer3-knowledge/src/api/app_monolith.py` (must remain a thin re-export of the canonical module with no local endpoint logic).
- CI guardrail: `services/layer3-knowledge/scripts/check_app_monolith_shim_drift.py` (fails when compatibility shim drifts from the approved re-export template).

## Layer 3 API model ownership note

- Canonical implementation: `value_fabric/layer3/api/models.py`.
- Compatibility shim only: `services/layer3-knowledge/src/api/models.py` (must only re-export canonical models; no local Pydantic model implementations).


## Layer 3 backup ownership boundary

- Canonical implementation: `value_fabric/layer3/backup/`.
- Compatibility wrappers only: `services/layer3-knowledge/src/backup/`.
- CI guardrail: `services/layer3-knowledge/scripts/check_backup_shim_drift.py` (fails when compatibility wrappers diverge from explicit forwarders).


## Required parity checkpoints (CI-enforced)

The CI suite validates canonical/runtime parity for each layer (`layer1`–`layer6`) across these checkpoints:

- **Route module parity:** maintained service route modules must re-export canonical route modules (shim-only behavior).
- **Service entrypoint parity:** maintained service entrypoints must expose `app` and serve non-empty OpenAPI contracts at `/openapi.json`.
- **Middleware chain anchor parity:** each layer declares a canonical middleware anchor module that must remain present.
- **Service/repository interface parity:** each layer declares canonical service and repository interface anchor files that must remain present and referenced by parity rules.

These checkpoints are asserted by:

- `tests/contract/test_layer_runtime_parity.py`
- `tests/contract/test_layer_service_entrypoint_smoke.py`

When adding or moving canonical modules, update parity rules in these tests in the same change to avoid drift.

## Related documentation

- [Repository Agent Rules (root)](../../AGENTS.md)
- [Source Tree Canonicalization](../source-tree-canonicalization.md)
- [Service Routing and API Version Matrix](./service-routing-and-api-version-matrix.md)
- [Quickstart](../getting-started/quickstart.md)

## Architecture sentinel map maintenance

`tests/arch/test_canonical_module_sentinels.py` intentionally tracks a small, high-impact
set of canonical module pairs.

When adding a new sentinel:

1. Prefer modules that are architectural choke points (for example shared API models or boundary schemas).
2. Add one `canonical_path` + `compatibility_path` pair to `SENTINELS`.
3. Keep compatibility module behavior shim-only (re-export/delegate); do not add local classes/functions there.
4. If a compatibility module temporarily needs local logic, document the migration exception in the test file with owner and removal date before merging.

Avoid adding low-value or highly volatile modules to keep this guardrail low-noise.


## Layer 4 namespace policy

- **Authoritative import namespace:** `value_fabric.layer4.*`.
- **Deprecated compatibility namespace:** `layer4_agents.*` (shims only; no net-new imports).
- **CI guardrail:** `scripts/ci/check_layer4_canonical_imports.py` with test coverage in `tests/ci/test_check_layer4_canonical_imports.py`.
