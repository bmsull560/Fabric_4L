# Kubernetes Container Hardening Summary (H-08 Remediation)

## Overview
Applied production-grade security hardening to all 10 Kubernetes deployments in `k8s/` directory to address H-08 audit finding.

## Changes Applied

### Pod-Level Security Context (All Deployments)
Added `securityContext` to all pod specs:
- `runAsNonRoot: true` - Prevents running as root
- `runAsUser: 1000` (or database-specific UIDs: 999 for postgres/redis, 7474 for neo4j)
- `runAsGroup: 1000` (or database-specific GIDs)
- `fsGroup: 1000` (or database-specific GIDs)  
- `seccompProfile: { type: RuntimeDefault }` - Uses default seccomp profile

### Container-Level Security Context (All Deployments)
Added `securityContext` to all containers:
- `allowPrivilegeEscalation: false` - Prevents privilege escalation
- `capabilities: { drop: ["ALL"] }` - Drops all Linux capabilities
- `readOnlyRootFilesystem: true` - For stateless services (not databases)

### Init Container Security (Layers 1-5)
Applied same container hardening to init containers:
- busybox init containers now run with security contexts
- Added resource requests/limits to init containers

### Startup Probes (All Application Containers)
Added `startupProbe` to containers with long initialization:
- Protects slow-starting containers during startup
- Higher failureThreshold to accommodate initialization time

### EmptyDir Volumes for /tmp (Stateless Services)
Added `emptyDir` volumes for services with `readOnlyRootFilesystem: true`:
- Mounted at `/tmp` for temporary file operations
- TMPDIR environment variable set to `/tmp`

## Files Modified

| File | Changes |
|------|---------|
| `layer1-ingestion.yml` | Pod securityContext, container securityContext (api + celery-worker), init container security, startup probes, tmp volumes, celery-worker probes, fixed celery module path |
| `layer2-extraction.yml` | Pod securityContext, container securityContext, init container security, startup probe, tmp volume |
| `layer3-knowledge.yml` | Pod securityContext, container securityContext, init container security, startup probe, tmp volume |
| `layer4-agents.yml` | Pod securityContext, container securityContext, init container security, startup probe, tmp volume |
| `layer5-ground-truth.yml` | Pod securityContext, container securityContext, init container security, startup probe, tmp volume |
| `layer6-benchmarks.yml` | Pod securityContext, container securityContext, startup probe, tmp volume |
| `frontend.yml` | Pod securityContext, container securityContext, startup probe, tmp volume |
| `postgres.yml` | Pod securityContext (UID 999), container securityContext (no readOnlyRootFilesystem) |
| `redis.yml` | Pod securityContext (UID 999), container securityContext (no readOnlyRootFilesystem) |
| `neo4j.yml` | Pod securityContext (UID 7474), container securityContext (no readOnlyRootFilesystem), startup probe |

## Database Exceptions

Databases (postgres, redis, neo4j) do NOT have `readOnlyRootFilesystem: true` because they require write access to:
- PostgreSQL: `/var/lib/postgresql/data` (PVC)
- Neo4j: `/data`, `/logs` (PVCs)

## Security Compliance

These changes bring the Kubernetes manifests in line with:
- Pod Security Standards (Restricted)
- CIS Kubernetes Benchmark
- Production hardening best practices

## Verification

Validate with:
```bash
# Check manifests are valid
kubectl apply --dry-run=client -f k8s/

# Verify security contexts after deployment
kubectl get pod -n value-fabric -o jsonpath='{.items[*].spec.securityContext}'
```

## Refinement Improvements

Post-implementation fixes applied (2026-05-03):
- **Startup probes added to all layers**: Added `startupProbe` to layer1-ingestion, layer2-extraction, layer3-knowledge, layer4-agents, layer5-ground-truth, layer6-benchmarks
  - `initialDelaySeconds: 10` (5 for layer6)
  - `periodSeconds: 5`
  - `timeoutSeconds: 3`
  - `failureThreshold: 30` (allows 2.5 minutes for slow startup)
- **Celery-worker probes**: Added missing liveness, readiness, and startup probes to celery-worker sidecar
- **Module path fix**: Corrected celery module path from `src.shared.tasks` to `layer1_ingestion.src.shared.tasks` (matching k8s/base/layer1-celery.yaml)
- **Startup probe consistency**: Standardized failureThreshold to 12 for most services
- **Comment cleanup**: Removed redundant comment block from layer5-ground-truth.yml

## Image Digest Pinning (Future Work)

Image digests (SHA256) should be pinned in CI/CD for reproducible deployments:
- Current: `value-fabric/layer1-ingestion:latest`
- Target: `value-fabric/layer1-ingestion@sha256:...`

### Image Provenance Strategy (Sprint 3)

**Current State:**
- Development: Uses `imagePullPolicy: Always` for all layer services
- Production: CI/CD should override branch tags with immutable digests (documented in layer1-ingestion.yml)
- No admission controller validation for image signatures or digests

**Recommended Approach:**
1. **Development**: Continue using branch tags (`:main`, `:staging`) with `imagePullPolicy: Always`
2. **Staging**: Use digest-pinned images from CI/CD build pipeline
3. **Production**: Require digest-pinned images with admission controller validation
4. **Admission Controller**: Implement Kyverno or OPA Gatekeeper policy to:
   - Enforce image digest format for production namespaces
   - Verify image signatures from trusted registry
   - Block images from untrusted registries

**Implementation Path:**
1. Add image digest validation script (placeholder for future admission controller)
2. Update CI/CD pipeline to output image digests
3. Configure admission controller policy for production namespace
4. Update manifests to reference digest-pinned images in production overlay
