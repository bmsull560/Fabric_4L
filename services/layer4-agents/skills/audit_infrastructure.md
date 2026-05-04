---
name: audit_infrastructure
description: Infrastructure security and compliance audit for Kubernetes, IaC, CI/CD pipelines, and secret management with drift detection and policy validation. Validates CIS benchmarks, container security, and environment parity.
allowed_agents: ["devops", "security-auditor", "sre", "pre-production-audit"]
---

# Audit Infrastructure Skill

## Purpose

This skill provides comprehensive infrastructure security auditing for the Value Fabric platform, including:
- Kubernetes security posture validation (CIS benchmarks)
- Infrastructure as Code (IaC) scanning and drift detection
- CI/CD pipeline security and compliance
- Container image vulnerability assessment
- Secret management and rotation validation
- Network policy coverage verification

## When to Use

- Pre-production infrastructure readiness validation
- Quarterly security assessments
- After Kubernetes upgrades or configuration changes
- During SOC 2/ISO 27001 audits
- Post-incident infrastructure hardening
- Environment parity verification before production deployment

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| audit_scope | string | No | "all" | Areas: all, kubernetes, iac, cicd, secrets, containers, networking |
| environments | string[] | No | ["staging", "production"] | Environments to audit |
| k8s_namespaces | string[] | No | ["default", "value-fabric"] | K8s namespaces to audit |
| run_iac_scanners | boolean | No | true | Run Checkov/Trivy config scanners |
| check_container_security | boolean | No | true | Validate container security |
| verify_network_policies | boolean | No | true | Verify K8s NetworkPolicy coverage |
| drift_detection | boolean | No | true | Detect infrastructure drift |
| severity_threshold | string | No | "medium" | Minimum severity: critical, high, medium, low |
| output_format | string | No | "markdown" | Output: markdown, json, sarif |
| fail_on_critical | boolean | No | true | Fail if critical findings detected |

## Audit Steps

### 1. Kubernetes Security Audit (CIS Benchmarks)

Validate K8s configurations against CIS Kubernetes Benchmark:

```bash
# Run kube-bench for CIS compliance
kube-bench run --targets node,etcd,policies,master

# Check Pod Security Standards
kubectl get podsecuritypolicy

# Verify RBAC configurations
kubectl auth can-i --list --all-namespaces
```

**CIS Control Categories:**

| Category | Controls | Key Checks |
|----------|----------|------------|
| Control Plane | 30+ | API server settings, etcd encryption |
| Worker Node | 20+ | Kubelet configuration, file permissions |
| Policies | 15+ | Pod Security Standards, Network Policies |
| Federated | 5+ | Multi-cluster security |

**Critical CIS Checks:**
- [ ] 1.2.7 - Ensure admission controller is enabled (Pod Security)
- [ ] 1.2.19 - Ensure Kubernetes API server certificate is valid
- [ ] 4.1.1 - Ensure kubelet service file permissions are 644
- [ ] 5.1.5 - Ensure default service accounts have limited access
- [ ] 5.3.2 - Ensure Service Account Tokens are only mounted where necessary

**Value Fabric Specific K8s Checks:**

```yaml
# Verify all layers have NetworkPolicies
network_policies:
  - namespace: value-fabric
    required_policies:
      - layer1-policy
      - layer2-policy
      - layer3-policy
      - layer4-policy
      - layer5-policy
      - layer6-policy
      - deny-all-default

# Verify SecurityContexts
security_contexts:
  - runAsNonRoot: true  # All containers
  - readOnlyRootFilesystem: true  # Where possible
  - allowPrivilegeEscalation: false  # All containers
```

### 2. Infrastructure as Code Scanning

Validate K8s manifests and configurations:

```bash
# Checkov scan for IaC issues
checkov --directory k8s/ --framework kubernetes --output sarif

# Trivy config scan
trivy config k8s/ --severity HIGH,CRITICAL

# Kustomize validation
kustomize build k8s/base | kubeval --strict
```

**IaC Security Checks:**

| Check | Tool | Severity | Description |
|-------|------|----------|-------------|
| CKV_K8S_8 | Checkov | High | Liveness probe not configured |
| CKV_K8S_22 | Checkov | Medium | Readiness probe not configured |
| CKV_K8S_28 | Checkov | High | Minimize admission of privileged containers |
| CKV_K8S_31 | Checkov | Medium | Ensure seccomp profile is set |

**Resource Limits Validation:**
```yaml
# All containers must have resource limits
resources:
  limits:
    cpu: "1000m"
    memory: "1Gi"
  requests:
    cpu: "100m"
    memory: "128Mi"
```

### 3. Container Security Audit

Scan container images for vulnerabilities:

```bash
# Build and scan each layer
for layer in layer1-ingestion layer2-extraction layer3-knowledge layer4-agents layer5-ground-truth layer6-benchmarks; do
  docker build -t $layer:scan value-fabric/$layer
  trivy image $layer:scan --severity HIGH,CRITICAL
  grype $layer:scan
  done

# Verify non-root execution
for layer in layer1 layer2 layer3 layer4 layer5 layer6; do
  docker run --rm --entrypoint id test-$layer -u
  done
```

**Container Security Requirements:**

| Requirement | Implementation | Verification |
|-------------|----------------|--------------|
| Non-root user | `USER appuser` or `USER node` | `id -u != 0` |
| Read-only root | `readOnlyRootFilesystem: true` | Mount verification |
| No privileged | `privileged: false` | K8s policy check |
| Distroless base | Use minimal images | Base image scan |
| No secrets in layers | Multi-stage builds | Layer inspection |

**Dockerfile Security Checklist:**
```dockerfile
# ✅ SECURE Dockerfile patterns
FROM python:3.11-slim as builder
# ... build steps ...

FROM python:3.11-slim
# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy only artifacts from builder
COPY --from=builder /app /app

# Set ownership and switch user
RUN chown -R appuser:appuser /app
USER appuser

# Read-only root filesystem
# (set in Kubernetes SecurityContext)
```

### 4. Secret Management Audit

Validate secret handling and Infisical integration:

```bash
# Verify External Secrets Operator is syncing
kubectl get externalsecrets -A

# Check for hardcoded secrets (local scan)
gitleaks detect --source . --verbose

# Verify secret rotation
curl -s http://localhost:8080/v1/secrets/rotation-status | jq
```

**Secret Management Requirements:**

| Requirement | Implementation | Evidence |
|-------------|----------------|----------|
| No hardcoded secrets | Pre-commit gitleaks | `.pre-commit-config.yaml` |
| External secret management | Infisical + ESO | `k8s/external-secrets/` |
| Automatic rotation | Quarterly rotation | `docs/runbooks/alertmanager-secret-management.md` |
| Audit logging | All secret access logged | `shared/audit/models.py` |
| Encryption at rest | K8s secret encryption | etcd encryption config |
| Encryption in transit | TLS for secret fetch | ESO configuration |

**Secret Rotation Validation:**
```python
SECRET_ROTATION_REQUIREMENTS = {
    "api_keys": {"max_age_days": 90, "auto_rotate": False},  # Manual review
    "db_credentials": {"max_age_days": 180, "auto_rotate": True},
    "jwt_secrets": {"max_age_days": 365, "auto_rotate": False},
    "oauth_tokens": {"max_age_days": 30, "auto_rotate": True},
}

# Verify each secret type meets rotation policy
```

### 5. CI/CD Pipeline Security

Validate GitHub Actions security:

```yaml
# Required security checks in workflows
security_gates:
  required_jobs:
    - gitleaks-scan        # Secret detection
    - trivy-image-scan     # Container scanning
    - sbom-policy          # SBOM generation
    - dast-api-scan        # OWASP ZAP
    - bandit-scan          # Python SAST
    - pip-audit-scan       # Dependency scan
    - frontend-security-audit  # NPM audit
    - dockerfile-non-root-check  # Container hardening
    - dependency-review    # GitHub dependency review
  
  required_artifacts:
    - sbom-*              # Every layer
    - security-evidence   # Consolidated evidence
    - dast-zap-reports    # DAST results
```

**CI/CD Security Checks:**

| Check | Implementation | Priority |
|-------|----------------|----------|
| Signed commits | Branch protection | P0 |
| Required reviews | CODEOWNERS + 2 reviews | P0 |
| Security gate blocking | `security-gates-required` job | P0 |
| No secrets in logs | Log masking in workflows | P1 |
| Principle of least privilege | Workflow permissions | P1 |
| SBOM generation | Trivy + Anchore | P1 |

### 6. Network Policy Validation

Verify zero-trust networking:

```bash
# Verify deny-all default is in place
kubectl get networkpolicy deny-all -n value-fabric -o yaml

# Check each layer has explicit policies
kubectl get networkpolicies -n value-fabric

# Test connectivity (should be restricted)
kubectl run test-pod --rm -it --image=busybox -- /bin/sh
# Try to reach other pods - should be blocked by default
```

**Required Network Policies per Namespace:**

```yaml
# Every layer namespace must have:
policies:
  - deny-all-default      # Block all by default
  - allow-dns             # CoreDNS access
  - allow-monitoring      # Prometheus scraping
  - layer-specific-policy # Layer-to-layer rules
  
# Layer3 Knowledge (sensitive) - extra policies:
extra_policies:
  - neo4j-access          # Restrict Neo4j access
  - postgres-access       # Restrict Postgres access
  - redis-access          # Restrict Redis access
```

### 7. Drift Detection

Detect infrastructure drift from GitOps state:

```bash
# Compare K8s state with Git repo
kubectl diff -f k8s/base/

# Check for manually created resources
kubectl get all -n value-fabric -o yaml | \
  grep -v "kubectl.kubernetes.io/last-applied-configuration"

# ArgoCD drift detection (if using)
argocd app diff value-fabric
```

**Drift Categories:**

| Drift Type | Detection | Risk |
|------------|-----------|------|
| Configuration drift | Kustomize diff | Medium |
| Image drift | Running vs. configured image | High |
| Resource drift | Manual K8s changes | High |
| Policy drift | Network policy bypass | Critical |
| Secret drift | Unsynced external secrets | Critical |

## Output Structure

### Summary

```markdown
## Infrastructure Audit: 92/100

**Critical:** 0 | **High:** 2 | **Medium:** 5 | **Low:** 8

**Environments:** staging, production
**Drift Detected:** No
**Compliance Pass Rate:** 96%

**High Priority Findings:**
- L4 NetworkPolicy allows broader egress than required
- Infisical secret rotation overdue (120 days vs. 90-day policy)
```

### Detailed Findings

**Kubernetes CIS Findings:**
```json
{
  "resource_type": "Pod",
  "namespace": "value-fabric",
  "name": "layer4-agents-xxx",
  "issue": "Container allows privilege escalation",
  "severity": "high",
  "cis_benchmark": "5.2.6",
  "remediation": "Add securityContext.allowPrivilegeEscalation: false"
}
```

**Container Security Findings:**
```json
{
  "image": "layer2-extraction:sha-abc123",
  "layer": "L2",
  "vulnerability_id": "CVE-2024-1234",
  "severity": "high",
  "package": "requests",
  "fixed_version": "2.31.0",
  "description": "Information disclosure in HTTP request handling"
}
```

**Secret Management Findings:**
```json
{
  "secret_name": "openai-api-key",
  "namespace": "value-fabric",
  "issue": "Secret age 120 days exceeds 90-day rotation policy",
  "severity": "medium",
  "recommendation": "Trigger secret rotation via Infisical UI or API"
}
```

## Example Usage

```bash
# Full infrastructure audit
python -m layer4_agents.tools.audit_infrastructure --environments staging,production

# Kubernetes security focus
python -m layer4_agents.tools.audit_infrastructure --audit-scope kubernetes

# CI/CD pipeline security
python -m layer4_agents.tools.audit_infrastructure --audit-scope cicd

# Drift detection only
python -m layer4_agents.tools.audit_infrastructure --drift-detection --environments production

# CI gate mode
python -m layer4_agents.tools.audit_infrastructure --fail-on-critical --output-format sarif
```

## Integration with Pre-Production Audit

This skill is automatically invoked by the `pre-production-audit` workflow when:
- K8s manifests are modified
- CI/CD workflows change
- Container images are rebuilt
- External Secrets configuration changes

## Safety Notes

- **Critical infrastructure findings block production deployment**
- Drift detection requires read-only K8s access
- Secret scanning runs locally (never in CI with real secrets)
- Container scanning uses cached vulnerability DB

## Related Skills

- `assess_drift` - Configuration drift across all layers
- `audit_compliance` - Infrastructure compliance (SOC 2 CC6/CC7)
- `audit_security` - Application-level security audit
