# Kubernetes Readiness & Deployment Test Suite

Comprehensive test coverage for the Value Fabric Kubernetes infrastructure, including CI validation, Kustomize overlays, Prometheus/Alertmanager monitoring, and security policies.

## Test Structure

| File | Coverage | Codemap References |
|------|----------|-------------------|
| `test_kustomize_overlays.py` | Base layer resources, dev/prod/staging overlays, Gateway API deployment, image pinning, replica patches | [2a], [2b], [2c], [2d], [2e], [2f] |
| `test_ci_validation.py` | kubeconform schema validation, conftest policies, kubectl dry-run | [1b], [1c], [1e] |
| `test_prometheus_monitoring.py` | Prometheus scrape configs, Alertmanager integration, alerting rules | [3a], [3b], [3c], [3d], [3e], [3f], [4a], [4b], [4c], [4d], [4e], [4f] |
| `test_security_policies.py` | OPA/Rego policies, Pod Security Standards, Kyverno policies, NetworkPolicies |
| `test_workload_validation.py` | Rollout strategies, health probes, resource constraints, image pinning, Layer 5 migrations | [5a], [5b], [5c], [5d], [5e], [5f] |
| `test_monitoring_validation.py` | monitoring-validation.sh script, alerting rules, recording rules | [6a], [6b], [6c], [6d], [6e], [6f], [7a], [7b], [7c], [7d], [7e], [7f] |
| `test_integration.py` | End-to-end pipeline, environment differences, cross-component integration |
| `test_network_policy_paths.py` | Denied/allowed network paths, selector precision, Istio principal-based identity enforcement |

## Running Tests

### Prerequisites

Install required tools (used by some integration tests):

```bash
# Kubernetes tools
brew install kustomize kubectl kubeconform  # macOS
# or
curl -sSL https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv5.4.3/kustomize_v5.4.3_linux_amd64.tar.gz | tar xz

# Policy tools
curl -sSL https://github.com/open-policy-agent/conftest/releases/download/v0.61.0/conftest_0.61.0_Linux_x86_64.tar.gz | tar xz

# Optional: OPA CLI for Rego validation
brew install opa  # macOS
```

### Run All Tests

```bash
# From repo root
pytest tests/k8s/ -v

# With coverage
pytest tests/k8s/ -v --cov=tests/k8s --cov-report=html
```

### Run Specific Test Files

```bash
# Kustomize overlay tests
pytest tests/k8s/test_kustomize_overlays.py -v

# CI validation tests
pytest tests/k8s/test_ci_validation.py -v

# Prometheus monitoring tests
pytest tests/k8s/test_prometheus_monitoring.py -v

# Security policy tests
pytest tests/k8s/test_security_policies.py -v

# Network policy path verification tests
pytest tests/k8s/test_network_policy_paths.py -v

# Workload validation tests
pytest tests/k8s/test_workload_validation.py -v
```

### Run by Codemap Reference

Tests are annotated with codemap location IDs for traceability:

```bash
# Tests related to kustomize build and CI validation
pytest tests/k8s/ -v -k "1b or 1c or 1e"

# Tests related to Prometheus scrape configs
pytest tests/k8s/ -v -k "3c or 3d"

# Tests related to Alertmanager routing
pytest tests/k8s/ -v -k "4a or 4c"
```

### Skip External Tool Tests

Tests that require external tools (kustomize, kubeconform, conftest) will auto-skip if tools are not available:

```bash
# Run only tests that don't require external tools
pytest tests/k8s/ -v --ignore-glob="*ci_validation*" --ignore-glob="*integration*"

# Or skip integration tests explicitly
pytest tests/k8s/ --ignore=tests/k8s/test_integration.py -v
```

## Test Coverage

### Kustomize Overlays ([1a], [1b], [2a]-[2f])

- ✅ Base kustomization includes all 6 layers + monitoring
- ✅ Dev overlay builds without errors
- ✅ Prod overlay extends base and applies patches
- ✅ Prod uses SHA256 digest pinning for images
- ✅ Prod replica patches scale workloads for HA
- ✅ Prod includes ExternalSecret resources (no raw Secrets)
- ✅ All resources have environment labels in prod

### CI Validation ([1b], [1c], [1e])

- ✅ Kustomize builds produce valid YAML
- ✅ kubeconform schema validation passes
- ✅ conftest security policy validation passes
- ✅ kubectl client dry-run passes
- ✅ Prod manifest contains ExternalSecrets, no raw Secrets

### Prometheus Monitoring ([3a]-[3f])

- ✅ ConfigMap has prometheus.yml and rules.yml
- ✅ All 6 layers have scrape jobs configured
- ✅ Alertmanager integration configured (target: alertmanager:9093)
- ✅ Layer 1 has custom metrics path (/api/v1/ingestion/metrics)
- ✅ Prometheus Deployment mounts ConfigMap for config
- ✅ Alert rules have ServiceDown and DependencyHealthDegraded

### Alertmanager Configuration ([4a]-[4f])

- ✅ Routing tree with group_by strategy
- ✅ Critical severity alerts routed to dedicated receiver
- ✅ Webhook receivers configured
- ✅ Inhibition rules suppress warnings when critical fires
- ✅ Alertmanager Deployment starts with config from ConfigMap

### Security Policies

- ✅ OPA/Rego policies check runAsNonRoot
- ✅ Rego policies check seccompProfile.type=RuntimeDefault
- ✅ Rego policies check container securityContext (allowPrivilegeEscalation, readOnlyRootFilesystem, drop ALL)
- ✅ All workloads have pod securityContext
- ✅ All containers have securityContext with hardening
- ✅ No privileged containers
- ✅ No containers running as root (uid=0)
- ✅ Kyverno policies exist for SLSA provenance and signature verification
- ✅ NetworkPolicies directory exists with YAML files

### Workload Validation ([5a]-[5f])

- ✅ All Deployments use RollingUpdate strategy
- ✅ All StatefulSets use RollingUpdate strategy
- ✅ All containers have liveness probes
- ✅ All containers have readiness probes
- ✅ All containers have resource requests (cpu, memory)
- ✅ All containers have resource limits (cpu, memory)
- ✅ No containers use :latest tag
- ✅ Prod images use SHA256 digests
- ✅ Layer 5 workloads have migration guardrails
- ✅ Init containers wait for dependencies ([5b])
- ✅ Secrets injected via secretKeyRef ([5c])
- ✅ Liveness probes configured ([5d])
- ✅ Readiness probes configured ([5e])
- ✅ Celery worker sidecars present where applicable ([5f])

### Monitoring Validation ([6a]-[6f], [7a]-[7f])

- ✅ monitoring-validation.sh script exists with valid syntax
- ✅ Script checks Prometheus targets health ([6a])
- ✅ Script checks Prometheus rules load status ([6b])
- ✅ Script checks Prometheus alerts status ([6c])
- ✅ Script checks Alertmanager status ([6d])
- ✅ Script includes alert pipeline smoke test ([6e], [6f])
- ✅ HighErrorRate alert covers all layers ([7a], [7b])
- ✅ Neo4jDown, PostgresDown, RedisDown alerts exist ([7c], [7d])
- ✅ WorkflowStalled alert exists ([7e], [7f])
- ✅ All alerts have runbook URLs
- ✅ All alerts have severity labels (critical/warning/info)

## Fixtures

The `conftest.py` provides shared fixtures:

- `repo_root` - Path to repository root
- `k8s_base_dir` - Path to k8s/base
- `k8s_overlays_dir` - Path to k8s/envs (legacy fixture name; resolves to `k8s/envs/`)
- `k8s_envs_dir` - Path to k8s/envs (canonical)
- `k8s_deployments_dir` - Path to k8s/deployments
- `k8s_policy_dir` - Path to k8s/policy
- `monitoring_dir` - Path to monitoring
- `load_yaml_documents` - Dict of all YAML documents from k8s/base
- `workload_documents` - Filtered list of workload resources only
- `kustomize_build_dev` - Rendered dev overlay YAML
- `kustomize_build_staging` - Rendered staging overlay YAML
- `kustomize_build_prod` - Rendered prod overlay YAML
- `skip_without_kustomize` - Skip marker if kustomize unavailable
- `skip_without_kubeconform` - Skip marker if kubeconform unavailable
- `skip_without_conftest` - Skip marker if conftest unavailable

## Adding New Tests

When adding new Kubernetes resources or changing configurations:

1. **Add tests to appropriate file** based on the component being tested
2. **Use existing fixtures** from `conftest.py` where possible
3. **Add codemap reference markers** in test docstrings (e.g., `[1b]`, `[3c]`)
4. **Update this README** with new coverage information
5. **Run full suite** before committing: `pytest tests/k8s/ -v`

### Test Pattern Example

```python
def test_my_new_feature(self, k8s_base_dir: Path) -> None:
    """[Xy] Description of what this test validates.
    
    Codemap reference: [Xy] - Links to codemap location ID
    """
    config = k8s_base_dir / "my-resource.yml"
    assert config.exists()
    
    with open(config) as f:
        doc = yaml.safe_load(f)
    
    # Assert expected structure
    assert doc.get("kind") == "ExpectedKind"
```

## CI Integration

Add a scheduled CI run (for example, nightly) that executes:

```bash
pytest tests/k8s/test_network_policy_paths.py -v
```

This catches drift in allowed/denied paths and identity enforcement before rollout.

These tests complement the GitHub Actions workflow at `.github/workflows/k8s-readiness.yml`:

- CI runs kustomize, kubeconform, conftest as validation steps
- These pytest tests validate the same behavior for local development
- Tests auto-skip if tools unavailable, ensuring they don't block development
- Integration tests simulate the full CI pipeline locally
