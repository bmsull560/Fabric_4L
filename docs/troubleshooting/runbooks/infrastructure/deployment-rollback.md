<!-- policy-ref: docs/operations/severity-escalation-policy.md -->
# Deployment Rollback Procedure

**Severity:** Applies to SEV-1, SEV-2, and any post-deploy regression
**Audience:** On-call SRE, service owners
**Last reviewed:** 2026-04-14

---

## When to Rollback

Initiate a rollback when **any** of the following conditions are met within the first 30 minutes after a deployment:

| Signal | Threshold | Source |
|--------|-----------|--------|
| 5xx error rate | > 5% for 2+ minutes | `HighErrorRate` alert / Grafana |
| Health check failures | Any layer failing readiness probe for > 60s | K8s events / PagerDuty |
| Latency regression | p95 exceeds SLO target by > 50% | Performance SLO dashboard |
| Data integrity issue | Any report of corrupted or missing data | Incident channel |
| Customer-facing impact | Confirmed user reports of failures | Support escalation |

## Prerequisites

- `kubectl` configured with production cluster context
- Cluster RBAC permissions for `apps/v1` Deployment resources in `value-fabric` namespace
- Access to the `#vf-incidents` Slack channel

## Rollback Steps

### 1. Announce the Rollback

```bash
# Post in #vf-incidents
"🔄 ROLLBACK INITIATED: Rolling back <service> deployment to previous revision. Reason: <brief reason>. ETA: 5 minutes."
```

### 2. Identify the Previous Good Revision

```bash
# List recent rollout history
kubectl -n value-fabric rollout history deployment/<service-name>

# Inspect a specific revision
kubectl -n value-fabric rollout history deployment/<service-name> --revision=<N>
```

### 3. Execute the Rollback

**Option A — Roll back to the immediately previous revision:**
```bash
kubectl -n value-fabric rollout undo deployment/<service-name>
```

**Option B — Roll back to a specific known-good revision:**
```bash
kubectl -n value-fabric rollout undo deployment/<service-name> --to-revision=<N>
```

### 4. Monitor the Rollout

```bash
# Watch rollout status (blocks until complete or failed)
kubectl -n value-fabric rollout status deployment/<service-name> --timeout=300s

# Verify pods are running the expected image
kubectl -n value-fabric get pods -l app=<service-name> -o jsonpath='{.items[*].spec.containers[*].image}'
```

### 5. Validate Service Health

```bash
# Check readiness/liveness probes are passing
kubectl -n value-fabric get pods -l app=<service-name>

# Hit the health endpoint directly
kubectl -n value-fabric port-forward deployment/<service-name> 8080:<service-port> &
curl -sf http://localhost:8080/health && echo "✅ Healthy" || echo "❌ Still unhealthy"
```

### 6. Verify Error Rate Recovery

- Open the **Value Fabric Operational** Grafana dashboard
- Confirm the 5xx error rate has returned to baseline (< 1%)
- Confirm p95 latency has returned within SLO targets
- Wait at least 5 minutes for stabilization

### 7. Announce Resolution

```bash
# Post in #vf-incidents
"✅ ROLLBACK COMPLETE: <service> rolled back to revision <N>. Error rate returned to baseline. Post-incident review scheduled."
```

## Service-Specific Notes

| Service | Deployment Name | Port | Health Path | Extra Considerations |
|---------|----------------|------|-------------|---------------------|
| L1 Ingestion | layer1-ingestion | 8000 | /api/v1/ingestion/health | Celery worker sidecar rolls back with deployment |
| L2 Extraction | layer2-extraction | 8000 | /health | Check Redis queue depth after rollback |
| L3 Knowledge | layer3-knowledge | 8003 | /health | Neo4j schema migrations are forward-only; verify compatibility |
| L4 Agents | layer4-agents | 8000 | /health | Check workflow state in Redis post-rollback |
| L5 Ground Truth | layer5-ground-truth | 8005 | /api/v1/health | DB migrations via initContainer; verify Alembic compatibility |
| L6 Benchmarks | layer6-benchmarks | 8006 | /health | Low-risk; only depends on L4 |
| Frontend | frontend | 3000 | / | Static assets; rollback is always safe |

## Database Migration Rollback

If the failing deployment included a database migration (L4 or L5):

1. **Check if the migration is backward-compatible.** Most migrations add columns/tables and are safe.
2. **If the migration is destructive** (dropped column, renamed table):
   - Do NOT rollback the deployment until the migration is manually reversed
   - Run: `alembic downgrade -1` from the service container
   - Then proceed with the deployment rollback

```bash
# Example: L5 Ground Truth migration rollback
kubectl -n value-fabric exec -it deployment/layer5-ground-truth -- \
  alembic downgrade -1
```

## Post-Rollback Actions

1. **File an incident** — All rollbacks require a documented incident
2. **Schedule postmortem** — Use `docs/runbooks/incident-postmortem-template.md`
3. **Root cause the failure** — Was it a code bug, config error, or infrastructure issue?
4. **Fix forward** — Prepare a corrected deployment and re-deploy through normal CI/CD
5. **Update this runbook** — If the rollback revealed a gap in this procedure

## Kustomize-Based Rollback (Alternative)

If using Kustomize overlays to manage image digests:

```bash
# Revert the image digest in the prod overlay
cd k8s/envs/prod
kustomize edit set image \
  services/<service>=ghcr.io/bmsull560/fabric_4l/<service>@sha256:<previous-known-good-digest>

# Apply
kustomize build . | kubectl apply -f -
```

## Escalation

If the rollback does **not** restore service health:

1. Escalate to **SEV-1** per `docs/operations/severity-escalation-policy.md`
2. Page the service owner and platform lead
3. Consider activating the DR plan: `docs/runbooks/dr-gameday-service-failover.md`
