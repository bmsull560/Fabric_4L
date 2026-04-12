# Value Fabric Kubernetes Deployment

Production-grade Kubernetes manifests for the Value Fabric platform.

## Prerequisites

- Kubernetes 1.24+
- kubectl configured
- Container images built and available in registry

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

## Monitoring

Prometheus metrics available at `/metrics` on all services.

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
