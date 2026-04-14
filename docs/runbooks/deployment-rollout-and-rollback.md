# Deployment Rollout, Canary/Blue-Green Criteria, and Rollback

## Scope

This runbook applies to Kubernetes deployments under `k8s/base/` and the CI/CD ephemeral deployment stage that:

1. Runs preflight checks.
2. Applies rendered manifests to an ephemeral Kubernetes cluster.
3. Executes post-deploy smoke checks for Layer 1–Layer 5 and the frontend.

---

## Rollout Strategy Requirements

All workloads in `k8s/base/` must define an explicit rollout strategy:

- `Deployment`: `spec.strategy.type: RollingUpdate` plus `maxUnavailable` and `maxSurge`.
- `StatefulSet` / `DaemonSet`: explicit `spec.updateStrategy`.

Preflight also requires, for every runtime container:

- `livenessProbe`
- `readinessProbe`
- `resources.requests` (`cpu`, `memory`)
- `resources.limits` (`cpu`, `memory`)
- pinned image tag or digest (no `:latest`)

---

## Canary vs Blue-Green Decision Criteria

Use the table below during release planning:

| Criterion | Prefer Canary | Prefer Blue-Green |
|---|---|---|
| Change blast radius | Medium/low-risk changes where gradual exposure is acceptable | High-risk, schema-sensitive, or wide-impact changes |
| Rollback speed required | Fast enough to reduce canary traffic back to 0% | Near-instant cutover to known-good stack required |
| Data/schema compatibility | Backward-compatible changes | Potentially incompatible behavior requiring environment isolation |
| Infrastructure capacity | Limited extra capacity | Sufficient capacity to run full parallel stacks |
| Verification style | Progressive SLO/error validation over time | Full pre-cutover validation and instant switch |

### Rule of thumb

- Default to **canary** for stateless service updates with backward-compatible contracts.
- Use **blue-green** for cross-layer changes, migration-sensitive releases, and when rollback must be nearly instantaneous.

---

## Standard Rollback Procedure

If smoke checks fail or production SLOs regress:

1. **Freeze rollout**
   - Pause automation and stop additional promotions.
2. **Identify failing component**
   - Check deployment status and pod events.
   - Check readiness probe failures and error-rate dashboards.
3. **Rollback**
   - For a `Deployment`: `kubectl rollout undo deployment/<name> -n value-fabric`
   - For blue-green: switch traffic back to the previous (blue) service/router target.
4. **Verify**
   - Wait for rollout completion.
   - Re-run smoke checks for L1–L5 and frontend.
5. **Escalate if persistent**
   - Follow service-specific runbook in this folder.
   - Open incident and include root cause plus corrective action.

---

## CI/CD Failure Handling

The preflight/deploy stage must fail fast when any required check is missing:

- schema/migration guardrails
- required secret references
- image tag pinning
- rollout strategy presence
- probe/resource requirements

Do not bypass failures by weakening checks; fix manifests or migration/secret contract gaps, then re-run pipeline.
