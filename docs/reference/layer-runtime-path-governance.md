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
| Layer 4 — Agents | `value_fabric/layer4/` | `services/layer4-agents/src/` (service bootstrap and compatibility surface) | `value_fabric/layer4/` | Layer 4 Maintainers — target review by **2026-09-30** |
| Layer 5 — Ground Truth | `services/layer5-ground-truth/src/layer5_ground_truth/` | `value_fabric/layer5/` (compatibility shims only) | `services/layer5-ground-truth/src/layer5_ground_truth/` | Layer 5 Maintainers — shim removal target review by **2026-09-30** |
| Layer 6 — Benchmarks | `value_fabric/layer6/` | `services/layer6-benchmarks/src/` (service wiring + compatibility shims) | `value_fabric/layer6/` | Layer 6 Maintainers — target review by **2026-09-30** |

## Contributor checklist (required)

Before opening a PR with backend runtime changes:

1. Confirm the target layer in this matrix.
2. Add net-new logic only to the canonical runtime path.
3. Keep service wrapper changes minimal and wiring-only.
4. If compatibility code is touched, add a TODO with migration intent and owner.

## Related documentation

- [Repository Agent Rules (root)](../../AGENTS.md)
- [Source Tree Canonicalization](../source-tree-canonicalization.md)
- [Service Routing and API Version Matrix](./service-routing-and-api-version-matrix.md)
- [Quickstart](../getting-started/quickstart.md)
