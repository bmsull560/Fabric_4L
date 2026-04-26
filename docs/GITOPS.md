# GitOps + Progressive Delivery Documentation

## Overview

Value Fabric implements GitOps with:
- **ArgoCD** for declarative application management
- **Argo Rollouts** for canary deployments
- **Flagger** (optional) for advanced traffic splitting
- **Feature flags** for controlled feature rollouts

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         GIT REPOSITORY                          │
├─────────────────────────────────────────────────────────────────┤
│  k8s/                                                           │
│    ├── base/                  (core workloads)                  │
│    ├── envs/{dev,prod}/       (env overlays)                    │
│    ├── routing/{nginx,        (routing stacks)                  │
│    │     gateway-api,istio}/                                    │
│    └── deployments/           (env + routing compositions;      │
│          dev-nginx/            ArgoCD/Flux sync targets)        │
│          prod-nginx/                                            │
│          prod-gateway-api/   (EXPERIMENTAL)                     │
│          prod-istio/         (EXPERIMENTAL)                     │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ARGOCD                                  │
├─────────────────────────────────────────────────────────────────┤
│  Application (dev)        → Auto-sync → value-fabric-dev        │
│  Application (staging)    → Auto-sync → value-fabric-staging  │
│  Application (production) → Manual sync → value-fabric-prod     │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ARGO ROLLOUTS / FLAGGER                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Canary Deployment:                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │   10%        │──▶│   50%        │──▶│   100%       │       │
│  │  Canary      │   │  Canary      │   │  Promote     │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│        │                  │                  │                │
│        ▼                  ▼                  ▼                │
│   Health Gates       Health Gates       Health Gates          │
│                                                                 │
│  Metrics: Success Rate, Latency, Error Rate                   │
│  Auto-rollback on failure                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FEATURE FLAGS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Production:                                                    │
│    FEATURE_ADVANCED_MODE: false (0% rollout)                  │
│    FEATURE_EXPERIMENTAL_AI: false (0% rollout)                  │
│                                                                 │
│  Staging:                                                       │
│    FEATURE_ADVANCED_MODE: true (100% rollout)                   │
│    FEATURE_EXPERIMENTAL_AI: true (50% rollout)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## GitOps Configuration

### ArgoCD Applications

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Apply Value Fabric applications
kubectl apply -f k8s/gitops/argocd-applications.yaml

# Access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### Environment Differences

| Environment | Sync Mode | Auto-rollback | Feature Flags |
|-------------|-----------|---------------|---------------|
| Dev | Automatic | Yes | All enabled |
| Staging | Automatic | Yes | Beta enabled |
| Production | Manual | Yes (pre-approved) | Controlled rollout |

## Progressive Delivery

### Canary Deployment Steps

1. **Pre-deployment Health Gate**
   - Environment health check
   - Resource availability
   - Error rate baseline
   - Database connectivity

2. **Canary Rollout**
   - 10% traffic → Pause 5min → Health check
   - 50% traffic → Pause 10min → Health check
   - 100% traffic → Promote

3. **Auto-rollback Triggers**
   - Success rate < 95%
   - P95 latency > 500ms
   - Error rate > 5%
   - Health check failures

### Analysis Templates

| Template | Metric | Threshold |
|----------|--------|-----------|
| success-rate | HTTP 2xx/3xx rate | >= 95% |
| latency | P95 response time | <= 500ms |
| error-rate | HTTP 5xx rate | < 1% |
| throughput | Requests/sec | >= 100 |

## Feature Flags

### Configuration

Feature flags are defined in `k8s/feature-flags/feature-flag-config.yaml`:

```yaml
# Production
FEATURE_ADVANCED_MODE: "false"      # Disabled
ROLLOUT_ADVANCED_MODE: "0"         # 0% rollout

# Staging
FEATURE_ADVANCED_MODE: "true"      # Enabled for all
ROLLOUT_ADVANCED_MODE: "100"       # 100% rollout
```

### Gradual Rollout Strategy

```
Week 1: 0% → 5%  (internal users)
Week 2: 5% → 25% (early adopters)
Week 3: 25% → 50% (beta group)
Week 4: 50% → 100% (general availability)
```

### Feature Dependencies

```
experimental_ai
  └── requires: advanced_mode
      └── requires: sso_oidc
```

## Operations

### Manual Rollback

```bash
# Via ArgoCD UI
1. Navigate to Applications → value-fabric-production
2. Click "Rollback"
3. Select previous revision
4. Click "Rollback"

# Via kubectl
kubectl argo rollouts abort layer4-agents -n value-fabric-prod
kubectl argo rollouts retry layer4-agents -n value-fabric-prod
```

### View Rollout Status

```bash
# Argo Rollouts CLI
kubectl argo rollouts get rollout layer4-agents -n value-fabric-prod --watch

# List experiments
kubectl argo rollouts list experiments -n value-fabric-prod

# List analysis runs
kubectl argo rollouts list analysisruns -n value-fabric-prod
```

### Override Health Gates

```bash
# Skip analysis for emergency deployment
kubectl annotate rollout layer4-agents -n value-fabric-prod \
  argoproj.io/skip-analysis="true"

# Manual promotion
kubectl argo rollouts promote layer4-agents -n value-fabric-prod
```

## Monitoring

### Key Metrics

| Metric | Query | Alert |
|--------|-------|-------|
| Canary success rate | `http_requests_total{service="*-canary"}` | < 95% |
| Canary latency | `histogram_quantile(0.99, ...)` | > 500ms |
| Rollout duration | `argo_rollout_info` | > 30min |
| Stuck rollouts | `argo_rollout_replicas_canary > 0 for 1h` | Yes |

### Dashboards

- ArgoCD: https://argocd.value-fabric.com
- Rollouts: Grafana dashboard "GitOps / Progressive Delivery"
- Feature flags: Admin panel → Feature Flags

## Troubleshooting

### Rollout Stuck

```bash
# Check analysis status
kubectl get analysisruns -n value-fabric-prod
kubectl describe analysisrun <name> -n value-fabric-prod

# Check metrics
kubectl argo rollouts get rollout layer4-agents -n value-fabric-prod
```

### Feature Flag Not Working

```bash
# Check ConfigMap is mounted
kubectl get configmap feature-flags -n value-fabric-prod -o yaml

# Restart deployment to pick up changes
kubectl rollout restart deployment/layer4-agents -n value-fabric-prod
```

### Sync Failures

```bash
# View ArgoCD events
kubectl get events -n argocd --field-selector involvedObject.kind=Application

# Check app conditions
kubectl get application value-fabric-production -n argocd -o yaml
```

## Best Practices

1. **Always use canary** for production deployments
2. **Set proper resource gates** before deployment
3. **Monitor during rollout** - don't walk away
4. **Feature flags first** - deploy code disabled, enable via flag
5. **Emergency stop** - Know how to abort/rollback quickly

## References

- [ArgoCD](https://argo-cd.readthedocs.io/)
- [Argo Rollouts](https://argoproj.github.io/argo-rollouts/)
- [Flagger](https://flagger.app/)
- [GitOps Principles](https://opengitops.dev/)
