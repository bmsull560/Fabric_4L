# Anti-Drift Hardening Deliverable

**Date:** 2026-05-12
**Scope:** Layer 3 focused, with repo-wide guardrail coverage for P0 drift categories
**Status:** Guardrails implemented and wired into CI. Baselines required for existing issues.

---

## Summary

Anti-drift hardening is complete for the implemented guardrail scope. These checks reduce regression risk and support production-readiness review, but full platform production readiness is not claimed unless all production gates pass with evidence.

---

## Guardrails Created

### 1. `scripts/ci/check_security_regressions.py` — NEW

Checks for:

- `debug_info` leaked in exception responses
- Infrastructure URIs in health-check JSON (`neo4j_uri` exposure)
- Fake health checks reporting `healthy` without actual I/O
- Redis `KEYS` in production code paths (requires `SCAN`)
- Broad `DeprecationWarning` suppression in pytest configs

**Result:**

```text
$ python scripts/ci/check_security_regressions.py --strict
Security regression findings: 0
PASS
```

### 2. `scripts/ci/check_deprecation_drift.py` — NEW

Checks for:

- `datetime.utcnow()` in source (Python 3.12 deprecation)
- Pydantic v1 APIs: `.parse_raw()`, `.parse_obj()`, `__root__`
- Invalid FastAPI response field types (`Request | None`)
- Broad deprecation warning suppression in pytest configs

**Result:**

```text
$ python scripts/ci/check_deprecation_drift.py --strict
Deprecation drift findings: 23
FAIL (existing issues outside Layer 3; baseline required)
```

**Findings outside Layer 3:**

- `services/layer4-agents/`: multiple `datetime.utcnow()` and `Request | None` usages
- `tests/`: multiple `datetime.utcnow()` in test code
- `scripts/perf/`: `datetime.utcnow()` in performance scripts

**Action:** Baseline file required at `docs/reference/deprecation-drift-baseline.json`.

### 3. `scripts/ci/check_migration_safety.py` — NEW

Checks for:

- `print()` in migration scripts (requires structured logging)
- Destructive Cypher without `MIGRATION_REVIEW_REQUIRED` marker
- Neo4j Enterprise-only constraints without Community fallback note
- Missing `dry_run` parameter

**Result:**

```text
$ python scripts/ci/check_migration_safety.py --strict
Migration safety findings: 47
FAIL (existing issues in Layer 4 migrations; baseline required)
```

**Action:** Baseline file required at `docs/reference/migration-safety-baseline.json`.

### 4. `scripts/ci/check_readiness_language.py` — NEW

Checks for unqualified production-readiness claims in reports/docs/CI:

- "production ready", "GA ready", "fully complete", "enterprise ready", "launch ready", "all gates pass"

**Result:**

```text
$ python scripts/ci/check_readiness_language.py --strict
Readiness language findings: 9
FAIL (existing unqualified claims in old reports; baseline or remediation required)
```

**Affected files:**

- `reports/repo-cleanup/BACKEND_TOPOLOGY_STATUS_2026-05-02.md`
- `reports/repo-cleanup/PYTEST_COLLECTION_REMEDIATION_REPORT_2026-05-02.md`
- `docs/comprehensive-platform-documentation.md`
- `docs/ValuePack_Framework_v2.0.md`
- `docs/archive/2026-04-27/ARCHIVED_MULTI_TENANCY_CONFIRMATION.md`
- `docs/validation/backend_integrated/final_evidence_report.md`

**Action:** Either update these files with approved boundary language or create a baseline.

---

## Guardrails Extended

### 5. `scripts/ci/check_deprecated_namespace_imports.py` — EXTENDED

Added `--check-shims` flag to detect service wrappers containing non-trivial domain logic (duplicate logic across `value_fabric/layer3/` and `services/layer3-knowledge/src/`).

**Result:**

```text
$ python scripts/ci/check_deprecated_namespace_imports.py --check-shims
Deprecated namespace import findings: 0
Shim logic violations: 0
PASS
```

### 6. `value_fabric/layer3/api/app_monolith.py` — EDITED (security fix)

Removed `neo4j_uri` from health check dependency details.

### 7. `value_fabric/layer3/api/routes/system.py` — EDITED (security fix)

Removed `neo4j_uri` from health check dependency details; added real Pinecone connectivity probe.

### 8. `.github/workflows/drift-check.yml` — EXTENDED

Added CI steps:

- Security regression drift
- Deprecation drift (with baseline)
- Migration safety drift (with baseline)
- Production-readiness language drift

---

## Drift Categories Now Covered

| Category | Script/Check | Status |
| - | - | - |
| Security regression | `check_security_regressions.py` | Active, passes |
| Deprecation drift | `check_deprecation_drift.py` | Active, needs baseline |
| Migration safety | `check_migration_safety.py` | Active, needs baseline |
| Readiness language | `check_readiness_language.py` | Active, needs baseline |
| Import/shim drift | `check_deprecated_namespace_imports.py --check-shims` | Active, passes |
| OpenAPI contract drift | `drift-check.yml` + `export_openapi.py` | Already existed, extended |

---

## Drift Categories Still Uncovered (P1/P2)

| Category | Rationale |
| - | - |
| Docker/base-image drift | Detect accidental public Python defaults in production Dockerfiles |
| PYTHONPATH/test-config drift | Prevent repo-root/service-local pytest path collisions |
| Frontend/backend route drift | Detect raw API paths outside approved client modules |
| Observability/metrics conventions | Verify no high-cardinality labels in metrics |
| Full cross-layer integration | Async contract tests across all layer boundaries |

---

## Known Exceptions / Allowlists

| Check | Exception | Reason |
| - | - | - |
| Security regression | `scripts/ci/check_security_regressions.py` self-allowlist | Script's own regex literals trigger false positives |
| Deprecation drift | `scripts/ci/check_deprecation_drift.py` self-allowlist | Script's own regex literals |
| Import drift | `value_fabric/layer3/` dual-role policy | `value_fabric/layer3/` is canonical domain; `services/layer3-knowledge/src/` is deployable wrapper |

---

## ADR-Required Items

1. **Canonical package authority:** Resolve whether `services/layer*-*/src/` or `value_fabric/layer*/` is the authoritative runtime source tree. Layer 3 currently uses a dual-role structure that contradicts `canonical-paths-policy.md`.

2. **Global-vs-tenant entity semantics:** Layer 3 has unresolved ambiguity about when entities are canonical/global vs. tenant-local. The Cypher scope guard enforces tenant filtering, but the semantic model should be explicitly documented.

---

## Baseline Files Required

To make the new checks pass in CI without fixing all existing issues:

1. `docs/reference/deprecation-drift-baseline.json`
   - Generate: `python scripts/ci/check_deprecation_drift.py --json > docs/reference/deprecation-drift-baseline.json`
   - Then restructure to wrap array under `"findings"` key.

2. `docs/reference/migration-safety-baseline.json`
   - Generate: `python scripts/ci/check_migration_safety.py --json > docs/reference/migration-safety-baseline.json`
   - Then restructure.

3. Readiness language baseline is optional; preferred approach is to update the 9 affected documents with approved boundary language.

---

## Production-Readiness Boundary Language

> Anti-drift hardening is complete for the implemented guardrail scope. These checks reduce regression risk and support production-readiness review, but full platform production readiness is not claimed unless all production gates pass with evidence.

---

## Commands to Validate

```bash
# Security regression (should pass)
python scripts/ci/check_security_regressions.py --strict

# Deprecation drift (needs baseline before --strict passes)
python scripts/ci/check_deprecation_drift.py --strict --use-baseline

# Migration safety (needs baseline before --strict passes)
python scripts/ci/check_migration_safety.py --strict --use-baseline

# Readiness language (fails on old reports; update docs or add baseline)
python scripts/ci/check_readiness_language.py --strict

# Import/shim drift (should pass)
python scripts/ci/check_deprecated_namespace_imports.py --check-shims

# CI workflow syntax check
python scripts/ci/check_workflow_references.py --workflow-glob drift-check.yml
```
