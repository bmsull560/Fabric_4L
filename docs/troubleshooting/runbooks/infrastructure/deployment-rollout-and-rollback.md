# Deployment Rollout and Rollback Runbook

## Overview

This runbook describes the deployment rollout strategy, rollback procedures, and decision criteria for canary vs blue-green deployments.

---

## Rollout Strategy

### RollingUpdate (Default)

All workloads use Kubernetes RollingUpdate strategy:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 25%
    maxUnavailable: 0
```

**Characteristics:**
- Gradual replacement of pods
- Zero-downtime deployments
- Automatic rollback on failed health checks
- Resource-efficient (no duplicate infrastructure)

---

## Deployment Flow

### 1. Preflight Checks (Mandatory)

```bash
python3 scripts/ci/k8s_preflight.py
```

**Validates:**
- Rollout strategy defined
- Liveness/readiness probes configured
- Resource limits set
- Images pinned (no :latest)
- Secret keys match template
- L5 migration guardrails present

**Gate:** PR fails if preflight checks fail.

---

### 2. Ephemeral Deploy and Smoke (CI)

```yaml
# .github/workflows/build-deploy.yml
deploy-ephemeral-and-smoke:
  steps:
    - Create kind cluster
    - Run preflight checks
    - Load SHA-tagged images
    - Apply k8s/deployments/dev-nginx manifests
    - Run post-deploy smoke checks (L1-L5 + frontend)
```

**Smoke checks:**
- `kubectl rollout status` for all deployments
- HTTP health checks on all services
- Fail fast on any check failure

---

### 3. Production Rollout

**Prerequisites:**
- [ ] Preflight checks passed
- [ ] Smoke tests passed in ephemeral environment
- [ ] Image SHA-tagged and pushed
- [ ] Manifests rendered for target environment

**Steps:**

```bash
# 1. Apply rendered manifests
kubectl apply -k k8s/deployments/prod-nginx

# 2. Monitor rollout
kubectl rollout status deployment/<service> -n prod --timeout=300s

# 3. Verify health
kubectl get pods -n prod
kubectl logs -l app=<service> -n prod --tail=50
```

---

## Rollback Procedures

### Automatic Rollback

Kubernetes automatically rolls back if:
- New pods fail liveness probes
- Rollout exceeds timeout
- Container exits with error

```bash
# Check rollout status
kubectl rollout status deployment/<service> -n prod

# View rollout history
kubectl rollout history deployment/<service> -n prod
```

### Manual Rollback

**When to use:**
- Post-deployment issue discovered (performance regression, bug)
- Data integrity concerns
- Security vulnerability in new version

**Steps:**

```bash
# 1. Identify previous revision
kubectl rollout history deployment/<service> -n prod

# 2. Rollback to previous revision
kubectl rollout undo deployment/<service> -n prod --to-revision=<N>

# 3. Verify rollback
kubectl rollout status deployment/<service> -n prod
kubectl get pods -n prod

# 4. Confirm service health
curl https://<service>/health
```

**After rollback:**
- Document reason in incident log
- Tag problematic image as `:<sha>-bad`
- Alert team via #deployments Slack

---

## Canary vs Blue-Green Decision Matrix

| Factor | Use Canary | Use Blue-Green |
|--------|------------|----------------|
| **Risk level** | Low-medium | High (critical services) |
| **Traffic split** | Gradual (5% → 25% → 50% → 100%) | Instant switch |
| **Infrastructure cost** | Low (shares existing pods) | High (duplicate infrastructure) |
| **Rollback speed** | Seconds (shift traffic) | Seconds (switch service) |
| **Complexity** | Medium (traffic shaping) | High (orchestration) |
| **Use case** | Feature flags, A/B tests | Database migrations, breaking changes |

### Current Implementation

**We use RollingUpdate (not canary/blue-green) by default because:**
- Kubernetes native, simple to operate
- Sufficient for current traffic patterns
- Zero-downtime with proper probes

**Future canary support:**
- Flagger or Argo Rollouts for progressive delivery
- Prometheus metrics-based promotion
- Automated rollback on error rate threshold

---

## Image Tagging Strategy

| Environment | Tag Pattern | Example |
|-------------|-------------|---------|
| Dev | `:<sha>-dev` | `:abc1234-dev` |
| Staging | `:<sha>-staging` | `:abc1234-staging` |
| Prod | `:<sha>` | `:abc1234` |
| Emergency rollback | `:<sha>-rollback` | `:abc1234-rollback` |

**Never use `:latest`** - preflight checks enforce this.

---

## Release Approval Criteria

A release is **APPROVED** when:

1. ✅ Preflight checks pass
2. ✅ Ephemeral smoke tests pass
3. ✅ Zero Trust Validation gate passes
4. ✅ Required reviewers approved PR
5. ✅ No overdue deprecations (or explicitly bypassed)

A release is **NO-GO** when any of:

- ❌ Preflight or smoke tests fail
- ❌ Zero Trust Validation gate fails
- ❌ Overdue deprecations not addressed
- ❌ Emergency freeze in effect

---

## Troubleshooting

### Rollout Stuck

```bash
# Check events
kubectl get events -n prod --field-selector involvedObject.name=<pod-name>

# Check pod logs
kubectl logs <pod-name> -n prod --previous

# Common causes:
# - Image pull error (check image SHA)
# - Resource quota exceeded
# - Node selector mismatch
# - ConfigMap/Secret missing
```

### Health Checks Failing

```bash
# Check probe configuration
kubectl describe pod <pod-name> -n prod | grep -A5 "Liveness\|Readiness"

# Test health endpoint manually
kubectl port-forward svc/<service> 8080:80 -n prod
curl http://localhost:8080/health
```

---

## Related Documentation

- [Zero Trust Validation](zero-trust-validation.md) - Security gate requirements
- [Backup and DR](backup-disaster-recovery.md) - Data protection during deployments
- [k8s/base manifests](../../k8s/base/) - Kubernetes configurations
