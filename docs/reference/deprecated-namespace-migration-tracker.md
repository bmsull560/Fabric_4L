# Deprecated Namespace Migration Tracker

## Objective

Drive internal imports of `value_fabric.layer1_ingestion` and `value_fabric.layer3_knowledge` to zero before shim removal.

## High-traffic importer tickets

- [ ] **VF-2411** Migrate top Layer 1 service importers to `value_fabric.layer1`.
- [ ] **VF-2412** Migrate top Layer 3 service importers to `value_fabric.layer3`.
- [ ] **VF-2413** Migrate remaining test-suite importers to canonical namespaces.
- [ ] **VF-2414** Remove deprecated shim imports from CI/scripts and generated developer tooling.
- [ ] **VF-2415** Final shim removal PR after scanner reports zero findings.

## Layered migration execution plan

### Layer 1 (`value_fabric.layer1_ingestion` → `value_fabric.layer1`) 

- [ ] L1-01: Service entrypoint import sweep (`services/layer1-ingestion/**` runtime and startup modules).
- [ ] L1-02: Shared utility import sweep (cross-layer utilities that still import Layer 1 shim).
- [ ] L1-03: Test importer sweep (`tests/**`, layer-specific fixtures, and contract tests).
- [ ] L1-04: Re-run architecture checks and record remaining Layer 1 deprecated-import count.

### Layer 3 (`value_fabric.layer3_knowledge` → `value_fabric.layer3`)

- [x] L3-01: Service entrypoint/shared utility migration for high-traffic importers (rate-limit admin utility now imports `value_fabric.layer3.db.driver`).
- [ ] L3-02: Service migration command/help text migration to canonical runtime namespace.
- [ ] L3-03: Test importer sweep (`tests/**`, integration fixtures, and contract tests).
- [ ] L3-04: Re-run architecture checks and record remaining Layer 3 deprecated-import count.

## Remaining import counts (architecture scanner)

- Layer 1 deprecated-import findings (non-compatibility code): **0**
- Layer 3 deprecated-import findings (non-compatibility code): **0**
- Baseline compatibility findings tracked for now: **0** (baseline file retained for CI gating behavior)

## Weekly progress log

- **2026-05-12:** Baseline policy/checks landed. Migration backlog opened; target is zero deprecated imports before 2026-08-31.
- **2026-05-12:** Added concrete Layer 1 + Layer 3 sub-tasks, migrated one high-traffic Layer 3 shared utility importer, and enabled CI baseline-aware gating to fail only net-new deprecated namespace imports.
