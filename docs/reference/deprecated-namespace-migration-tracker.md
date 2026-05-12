# Deprecated Namespace Migration Tracker

## Objective

Drive internal imports of `value_fabric.layer1_ingestion` and `value_fabric.layer3_knowledge` to zero before shim removal.

## High-traffic importer tickets

- [ ] **VF-2411** Migrate top Layer 1 service importers to `value_fabric.layer1`.
- [ ] **VF-2412** Migrate top Layer 3 service importers to `value_fabric.layer3`.
- [ ] **VF-2413** Migrate remaining test-suite importers to canonical namespaces.
- [ ] **VF-2414** Remove deprecated shim imports from CI/scripts and generated developer tooling.
- [ ] **VF-2415** Final shim removal PR after scanner reports zero findings.

## Weekly progress log

- **2026-05-12:** Baseline policy/checks landed. Migration backlog opened; target is zero deprecated imports before 2026-08-31.
