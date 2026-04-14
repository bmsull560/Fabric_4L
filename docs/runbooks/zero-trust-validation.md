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
3. Patch control and add/adjust tests without weakening existing protections.
4. Re-run zero-trust validation and confirm green status before re-requesting approval.
