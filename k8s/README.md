# Value Fabric Kubernetes Deployment

Production-grade Kubernetes manifests for the Value Fabric platform.

This directory supports both:
- Legacy flat manifests (`kubectl apply -f k8s/`) for compatibility.
- Canonical Kustomize deployments (`k8s/base`, `k8s/overlays/dev`, `k8s/overlays/prod`) for production readiness.

## Prerequisites

- Kubernetes 1.24+
- kubectl configured
- Container images built and available in registry
- **metrics-server** installed (required for HorizontalPodAutoscaler)

## Security Hardening

This deployment includes production-grade security controls:

### Pod Security Contexts

All deployments run with:
- Non-root user (UID 1000)
- Read-only root filesystem
- Dropped all capabilities
- No privilege escalation
- Runtime default seccomp profile

### Network Policies

Zero-trust network segmentation is enforced via `k8s/network-policies/`:
- Default deny-all for ingress/egress
- Explicit allow rules for required service-to-service communication
- DNS resolution allowed cluster-wide
- Layer-specific policies enforce least-privilege access

### Horizontal Pod Autoscaler (HPA)

Auto-scaling configured for:
- **layer2-extraction**: 2-6 replicas at 70% CPU
- **layer4-agents**: 2-10 replicas at 70% CPU / 80% memory
- **frontend**: 2-8 replicas at 70% CPU

**Scaling Behavior:**
- Scale-up: 100% increase per minute after 60s stabilization
- Scale-down: 50% decrease per minute after 300s stabilization (prevents flapping)

Requires metrics-server: `kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml`

### Pod Disruption Budgets

Critical services maintain availability during disruptions:
- **layer4-agents**: `minAvailable: 1`

### Image Pinning

Production overlay uses SHA256 digest pinning (immutable references):
```bash
# CI updates digests via:
kustomize edit set image "ghcr.io/bmsull560/fabric_4l/layer4-agents@sha256:abc123..."
```

## Recommended: Kustomize Deployment

Deploy using overlays for environment-specific behavior.

```bash
# Render manifests
kubectl kustomize k8s/overlays/dev
kubectl kustomize k8s/overlays/prod

# Validate against API server (recommended in staging/prod clusters)
kubectl apply --dry-run=server -k k8s/overlays/dev
kubectl apply --dry-run=server -k k8s/overlays/prod

# Deploy
kubectl apply -k k8s/overlays/dev
# or
kubectl apply -k k8s/overlays/prod
```

### Overlay Policy

- `dev` overlay: pragmatic defaults for local/staging iteration. Uses placeholder SHA digests (will fail without image build).
- `prod` overlay: **SHA256 digest pinned images** (immutable), higher replica counts, production resource settings.

## Deployment Order

Deploy in this order to satisfy dependencies:

```bash
# 1. Create namespace
kubectl apply -f namespace.yml

# 2. Create secrets (review and update secrets.yml first!)
# For development:
kubectl apply -f secrets.yml

# For production with Vault (requires External Secrets Operator):
# kubectl apply -f external-secrets/vault-integration.yml

# 3. Create config maps
kubectl apply -f configmap-global.yml

# 4. Deploy infrastructure (Neo4j, Postgres, Redis)
kubectl apply -f neo4j.yml
kubectl apply -f postgres.yml
kubectl apply -f redis.yml

# Wait for infrastructure to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n value-fabric --timeout=120s
kubectl wait --for=condition=ready pod -l app=redis -n value-fabric --timeout=60s
kubectl wait --for=condition=ready pod -l app=neo4j -n value-fabric --timeout=180s

# 5. Deploy application layers L1-L4
kubectl apply -f layer1-ingestion.yml
kubectl apply -f layer2-extraction.yml
kubectl apply -f layer3-knowledge.yml
kubectl apply -f layer4-agents.yml

# Wait for L1-L4 to be ready (required for L5/L6 dependencies)
kubectl wait --for=condition=ready pod -l app=layer1-ingestion -n value-fabric --timeout=120s
kubectl wait --for=condition=ready pod -l app=layer2-extraction -n value-fabric --timeout=120s
kubectl wait --for=condition=ready pod -l app=layer3-knowledge -n value-fabric --timeout=120s
kubectl wait --for=condition=ready pod -l app=layer4-agents -n value-fabric --timeout=120s

# 6. Deploy application layers L5-L6
kubectl apply -f layer5-ground-truth.yml
kubectl apply -f layer6-benchmarks.yml

# 7. Deploy monitoring stack
kubectl apply -f monitoring-alertmanager.yml
kubectl apply -f monitoring-prometheus.yml

# Verify all services
kubectl get pods -n value-fabric
```

## Quick Deploy All

```bash
kubectl apply -f .
```

## Service Dependencies

```
layer1-ingestion → postgres, redis
layer2-extraction → redis, neo4j
layer3-knowledge → neo4j, redis
layer4-agents → redis, neo4j, postgres
layer5-ground-truth → postgres, layer3-knowledge
layer6-benchmarks → (standalone - no deps)
frontend → layer4-agents, layer5-ground-truth, layer6-benchmarks
```

## Health Checks

All services expose health endpoints:

| Service | Health Endpoint |
|---------|-----------------|
| layer1 | `/api/v1/ingestion/health` |
| layer2 | `/health` |
| layer3 | `/health` |
| layer4 | `/health` |
| layer5 | `/api/v1/health` |
| layer6 | `/health` |
| frontend | `/` |

## Monitoring

Prometheus metrics available at `/metrics` on all services.

Monitoring manifests:

- `monitoring-alertmanager.yml`
- `monitoring-prometheus.yml`

Runtime verification playbook:

```bash
# Forward monitoring services locally
kubectl port-forward -n value-fabric svc/prometheus 9090:9090
kubectl port-forward -n value-fabric svc/alertmanager 9093:9093

# Verify target health and scrape status
curl -fsS http://localhost:9090/api/v1/targets

# Verify loaded rules and evaluation health
curl -fsS http://localhost:9090/api/v1/rules

# Verify active alerts in Prometheus
curl -fsS http://localhost:9090/api/v1/alerts

# Verify Alertmanager pipeline endpoint
curl -fsS http://localhost:9093/api/v2/status

# Smoke an alert directly into Alertmanager
curl -X POST http://localhost:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[{"labels":{"alertname":"Task46Smoke","severity":"warning"},"annotations":{"summary":"Task 46 smoke alert"}}]'
```

## Secrets Management

**WARNING**: Default secrets are provided for development only.

For production:
1. Use external secrets management (Vault, AWS Secrets Manager, etc.)
2. Or use Sealed Secrets / External Secrets Operator
3. Never commit real secrets to git

## Resource Requirements

| Component | CPU Request | Memory Request | CPU Limit | Memory Limit |
|-----------|-------------|----------------|-----------|--------------|
| Neo4j | 500m | 2Gi | 2000m | 4Gi |
| Postgres | 100m | 256Mi | 500m | 1Gi |
| Redis | 100m | 128Mi | 500m | 512Mi |
| Layer 1-6 | 100m | 128Mi | 500m | 512Mi |

## Persistent Storage

| PVC | Size | Purpose |
|-----|------|---------|
| neo4j-data | 20Gi | Neo4j graph data |
| neo4j-logs | 5Gi | Neo4j logs |
| postgres-pvc | 10Gi | PostgreSQL data |

## Troubleshooting

Check pod status:
```bash
kubectl get pods -n value-fabric
```

View logs:
```bash
kubectl logs -n value-fabric deployment/layer5-ground-truth
```

Check service endpoints:
```bash
kubectl get svc -n value-fabric
```

Port forward for local testing:
```bash
kubectl port-forward -n value-fabric svc/layer5-ground-truth 8005:8005
```

## Migration Note

Flat manifests are intentionally preserved during migration. New CI and production checks should target Kustomize overlays first.
