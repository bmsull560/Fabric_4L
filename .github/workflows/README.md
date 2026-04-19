# GitHub Actions Workflows

## Overview

This directory contains 21 CI/CD workflows for the Fabric_4L 6-layer enterprise agentic SaaS platform.

## Workflow Tiers

### Required (PR Merge Blocking)
These workflows must pass before a PR can be merged:

| Workflow | Purpose | Trigger |
|----------|---------|---------|
| `pr-checks.yml` | Multi-layer lint, typecheck, tests, security scan, dependency audit | PR to main |
| `contract-checks.yml` | Cross-layer contract tests | PR to main |
| `security-gates.yml` | SAST scanning (Semgrep/CodeQL) | PR/Push |
| `k8s-dry-run.yml` | Kubernetes manifest validation | PR to main |

### Nightly/Scheduled (Deep Assurance)
Run periodically for comprehensive validation:

| Workflow | Purpose | Trigger |
|----------|---------|---------|
| `integration-tests.yml` | Full Docker-based integration test suite | Schedule, Manual |
| `smoke-gate.yml` | Cross-layer smoke tests | PR (optional) |
| `performance-load-tests.yml` | K6 load testing | Schedule, Manual |
| `contract-drift-check.yml` | OpenAPI contract validation | Schedule |
| `ai-evals-pipeline.yml` | Agent skill validation | PR to skills/, Schedule |
| `chaos-testing.yml` | Litmus chaos experiments | Schedule |
| `secret-rotation.yml` | Automated secret rotation | Schedule |

### Optional/Manual (On-Demand)
Run manually when needed:

| Workflow | Purpose | Trigger |
|----------|---------|---------|
| `build-deploy.yml` | Docker builds, image signing | Push to main, Manual |
| `deploy.yml` | GitOps deployment via ArgoCD | Push to main, Manual |
| `environment-promotion.yml` | Dev→Staging→Prod promotion gates | Build success, Manual |
| `vault-integration.yml` | Dynamic secret injection | Reusable workflow |
| `penetration-testing.yml` | Security pentest suite | Manual |
| `zero-trust-validation.yml` | Security policy validation | PR (informational) |
| `supply-chain.yml` | SBOM, Cosign signing | Build completion |
| `test-reporting.yml` | Aggregate test results | PR Checks completion |
| `package-sign.yml` | Package signing | Manual |
| `publish-sdk.yml` | SDK publishing | Manual |
| `regenerate-sdk.yml` | SDK regeneration | Manual |
| `openapi-drift-check.yml` | OpenAPI drift detection | Schedule |
| `pr-performance-gate.yml` | Performance regression | PR (optional) |
| `preflight.yml` | Environment validation | Manual |
| `runbook-validation.yml` | Runbook checks | PR |
| `security-validation.yml` | Extended security tests | Manual |
| `audit-evidence.yml` | Audit evidence collection | Schedule |
| `billing-entitlements-regression.yml` | Billing regression tests | PR |
| `docker-build-check.yml` | Dockerfile validation | PR |
| `alertmanager-config-check.yml` | Alertmanager validation | PR |

## Workflow Inventory (Detailed)

### Core CI Workflows

| Workflow | Purpose | Trigger | Status |
|----------|---------|---------|--------|
| `pr-checks.yml` | Multi-layer Python/Node linting, type checks, tests | PR to main/develop | ✅ Active |
| `build-deploy.yml` | Docker builds, ephemeral Kind clusters, image signing | Push to main | ✅ Active |
| `contract-drift-check.yml` | OpenAPI contract validation | Schedule/PR | ✅ Active |

### NEW: Unified Test Reporting (Priority 1)

| Workflow | Purpose | Trigger | Status |
|----------|---------|---------|--------|
| `test-reporting.yml` | Aggregate test results, post PR coverage comments | PR Checks / Integration Tests completion | ✅ **NEW** |

**Features:**
- Parses JUnit XML from all 6 layers + frontend
- Calculates coverage deltas against baseline
- Posts consolidated PR comment with per-layer results table
- Creates GitHub Check Run with test summary

### NEW: Environment Promotion (Priority 2)

| Workflow | Purpose | Trigger | Status |
|----------|---------|---------|--------|
| `environment-promotion.yml` | Automated Dev→Staging→Prod promotion gates | Build success / Manual dispatch | ✅ **NEW** |

**Features:**
- **Dev**: Auto-deploy on build success, no approval required
- **Staging**: Creates promotion PR, requires QA approval
- **Production**: Manual approval, Argo Rollouts canary analysis
- Automatic rollback on deployment failure
- Slack notifications for production deployments

### NEW: Vault Integration (Priority 3)

| Workflow | Purpose | Trigger | Status |
|----------|---------|---------|--------|
| `vault-integration.yml` | OIDC authentication, dynamic secret injection | Reusable workflow | ✅ **NEW** |

**Features:**
- OIDC JWT authentication to HashiCorp Vault
- Fetches secrets per environment (dev/staging/prod)
- Automatic secret masking in logs
- Audit logging for compliance
- Dynamic credential rotation support

### NEW: AI Evaluation Pipeline (Priority 4)

| Workflow | Purpose | Trigger | Status |
|----------|---------|---------|--------|
| `ai-evals-pipeline.yml` | Validate agent skills against ground truth | PR to skills/agents/prompts | ✅ **NEW** |

**Features:**
- Discovers changed skills from PR diff
- Runs per-skill evaluation tests
- Golden trace validation (85% threshold)
- Baseline comparison against main branch
- PR comment with pass/fail status
- Deployment gate: blocks merge on eval failures

### Security Workflows

| Workflow | Purpose | Trigger | Status |
|----------|---------|---------|--------|
| `security-gates.yml` | SAST scanning (Semgrep/CodeQL) | PR/Push | ✅ Active |
| `supply-chain.yml` | SBOM, Cosign signing, provenance | Build completion | ✅ Active |
| `zero-trust-validation.yml` | Security policy validation | PR | ✅ Active |
| `secret-rotation.yml` | Automated secret rotation | Schedule | ✅ Active |

### Testing Workflows

| Workflow | Purpose | Trigger | Status |
|----------|---------|---------|--------|
| `smoke-gate.yml` | Cross-layer integration smoke tests | PR | ✅ Active |
| `integration-tests.yml` | Full integration test suite | PR/Schedule | ✅ Active |
| `performance-load-tests.yml` | K6 load testing | Schedule/Manual | ✅ Active |
| `chaos-testing.yml` | Litmus chaos experiments | Schedule | ✅ Active |

### Deployment Workflows

| Workflow | Purpose | Trigger | Status |
|----------|---------|---------|--------|
| `deploy.yml` | GitOps deployment via ArgoCD | Push to main | ✅ Active |
| `k8s-readiness.yml` | K8s cluster validation | Pre-deploy | ✅ Active |

## Workflow Dependencies

```
PR Checks
    ↓ (on success)
Build & Deploy
    ↓ (on success)
Environment Promotion
    ├── Auto: Dev deployment
    ├── PR: Staging promotion (needs approval)
    └── PR: Production promotion (needs approval)

PR Checks / Integration Tests
    ↓ (on completion)
Unified Test Reporting
    └── PR comment with coverage deltas

Skill/Agent/Prompt changes
    ↓
AI Evaluation Pipeline
    ├── Per-skill validation
    ├── Golden trace evals
    └── Deployment gate
```

## Key Improvements

### 1. Test Visibility (test-reporting.yml)
- **Before**: Test results scattered across 6 different artifacts
- **After**: Unified PR comment with per-layer breakdown and coverage deltas

### 2. Environment Promotion (environment-promotion.yml)
- **Before**: Manual promotion process, no approval gates
- **After**: Automated PR-based promotion with QA/Lead approval workflows

### 3. Secrets Management (vault-integration.yml)
- **Before**: Hardcoded secrets in GitHub Actions
- **After**: Dynamic secret injection from Vault with OIDC auth

### 4. AI Quality Gates (ai-evals-pipeline.yml)
- **Before**: No validation for agent skills/prompts
- **After**: Mandatory evaluation tests with 85% pass threshold

## Usage Examples

### Trigger Environment Promotion Manually
```bash
gh workflow run environment-promotion.yml \
  -f environment=staging \
  -f image_tag=sha-abc123
```

### Use Vault Integration in Another Workflow
```yaml
jobs:
  deploy:
    uses: ./.github/workflows/vault-integration.yml
    with:
      environment: staging
      secrets_path: secret/data/fabric/staging
    secrets:
      VAULT_ADDR: ${{ secrets.VAULT_ADDR }}
      VAULT_ROLE: ${{ secrets.VAULT_ROLE_STAGING }}
```

### Run AI Evals Manually
```bash
gh workflow run ai-evals-pipeline.yml \
  -f eval_target=assess_drift \
  -f baseline_comparison=true
```

## Artifact Naming Convention

Test results use standardized naming for the unified reporting:
- `test-results-layer1-ingestion/` - Layer 1 JUnit XML + coverage
- `test-results-layer2-extraction/` - Layer 2 JUnit XML + coverage
- `test-results-layer3-knowledge/` - Layer 3 JUnit XML + coverage
- `test-results-layer4-agents/` - Layer 4 JUnit XML + coverage
- `test-results-layer5-ground-truth/` - Layer 5 JUnit XML + coverage
- `test-results-layer6-benchmarks/` - Layer 6 JUnit XML + coverage
- `test-results-frontend/` - Frontend JUnit XML
- `contract-test-results/` - Cross-layer contract tests

## Compliance & Security

- All workflows use OIDC for cloud authentication (no long-lived secrets)
- Vault integration provides dynamic secret rotation
- SBOMs generated and signed with Cosign
- SAST scanning with Semgrep and CodeQL
- Supply chain security with dependency auditing

## Maintenance

- Review workflow run logs weekly for deprecation warnings
- Update action versions quarterly
- Rotate OIDC roles annually
- Review Vault policies on environment changes
