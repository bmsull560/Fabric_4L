# Zero-Trust Validation Runbook

## Purpose

Define testable, repeatable checks that prove tenant boundaries are enforced across L1-L6 and publish machine-readable evidence for CI/nightly and release approval.

---

## Validation profile

- **Execution modes**
  - PR/CI: required gate for merges to `main`
  - Nightly: scheduled evidence collection + drift detection
- **Evidence location (CI artifact):** `zero-trust-evidence/`
- **Evidence retention:** 30 days (configurable in workflow)

---

## Testable zero-trust checks

### ZT-1 — Network policy deny-by-default

**Goal:** Verify namespace baseline deny policy exists and layer-specific allowlists are present.

**Checks:**
1. `k8s/base/network-policies/deny-all.yml` exists with `kind: NetworkPolicy`.
2. `k8s/base/network-policies/kustomization.yaml` includes `deny-all.yml`.
3. Layer allowlist policies exist for layer1..layer6 and frontend.

**Pass criteria:** all artifacts exist and references are present.

---

### ZT-2 — Cross-tenant access attempt rejection

**Goal:** Ensure cross-tenant access is blocked by tenant-scoped controls.

**Checks (static + test harness):**
1. Tenant-scoping primitives present (`TenantScopedMixin`, `TenantScopedCypher`, `tenant_cache_key`).
2. Identity middleware resolves tenant from verified identity.
3. Shared identity test suite includes tenant claim validation.
4. Cross-layer tenant isolation matrix evidence is present at `artifacts/mandatory_security/cross_layer_tenant_isolation_matrix.json`.
5. Matrix controls pass for every layer `L1` through `L6` and every control ID:
   - `CTX-001`
   - `READ-001`
   - `WRITE-001`
   - `QUERY-001`
   - `FAIL-001`

**Pass criteria:** all required primitives and tests are present; any missing control fails gate.

> Note: Runtime A→B synthetic attack tests should be added as integration tests in cluster once stable seeded fixtures for multi-tenant data are available.

---

### ZT-3 — Service-to-service auth enforcement

**Goal:** Ensure every service call path is authenticated/authorized, not just network-allowed.

**Checks:**
1. Middleware supports `Authorization` bearer JWT or API key path.
2. Authorization dependencies expose `require_role` and `require_permission` controls.
3. Layer configuration enforces non-trivial JWT secret requirements.

**Pass criteria:** authn/authz controls found and no missing mandatory control file.

---

## CI and nightly automation

Workflow: **`.github/workflows/zero-trust-validation.yml`**

- Triggers:
  - `pull_request` to `main`
  - `push` to `main`
  - nightly schedule (`0 3 * * *`)
  - `workflow_dispatch`
- Runs `scripts/security/zero_trust_checks.sh`
- Publishes artifact bundle:
  - `summary.md`
  - `network_policy_checks.json`
  - `tenant_isolation_checks.json`
  - `service_auth_checks.json`

---

## Release approval criteria (required gate)

A release **must not** be approved unless all are true:

1. The latest run of **Zero Trust Validation / zero-trust-gate** on the release commit is green.
2. Evidence artifact bundle is attached and includes all three JSON evidence files.
3. No failed check in `summary.md`.
4. Branch protection for the release branch marks this check as **required**.

If any condition fails, release status is **NO-GO** until remediated.

---

## Local execution

```bash
bash scripts/security/zero_trust_checks.sh
```

Artifacts are written to `artifacts/zero-trust/`.

---

## Incident handling for failed gate

1. Inspect `summary.md` in the uploaded artifact.
2. Identify failing control family (`network`, `tenant-isolation`, `service-auth`).
3. For `tenant-isolation` failures, open `artifacts/mandatory_security/cross_layer_tenant_isolation_matrix.json` and locate the failing `layer` + `control_id` tuple.
4. Use the matrix control mapping for triage:
   - `CTX-001`: request handler is not treating authenticated tenant context as authoritative.
   - `READ-001`: representative read path can expose Tenant B data to Tenant A.
   - `WRITE-001`: representative write or mutation path is accepting Tenant B targeting from Tenant A.
   - `QUERY-001`: repository or query layer is missing an explicit tenant filter.
   - `FAIL-001`: endpoint or handler does not fail closed when tenant context is absent.
5. Patch the affected layer without weakening existing protections, then re-run `bash scripts/ci/mandatory_security_regression_gate.sh`.
6. Confirm the regenerated matrix artifact reports `overall_status: PASS` before re-requesting approval.
