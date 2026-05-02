---
name: pre_production_audit
description: Orchestrated pre-production audit workflow that coordinates all specialized audit skills (AI systems, compliance, performance, infrastructure) into a unified production readiness assessment.
triggers: ["production-deploy-request", "quarterly-audit", "major-release", "compliance-audit"]
allowed_agents: ["pre-production-auditor", "release-manager", "platform-team"]
---

# Pre-Production Audit Workflow

## Purpose

This workflow orchestrates comprehensive pre-production auditing by coordinating multiple specialized audit skills into a unified assessment. It ensures all critical areas (security, compliance, AI/ML, performance, infrastructure) are validated before production deployment.

## When to Trigger

- Production deployment request submitted
- Quarterly production readiness review
- Major version release (breaking changes)
- Post-incident full assessment
- SOC 2 / GDPR audit preparation
- After significant architectural changes

## Workflow Orchestration

### Phase 1: Parallel Audit Execution

Execute independent audits in parallel for speed:

```yaml
parallel_jobs:
  - job: ai_systems_audit
    skill: audit_ai_systems
    params:
      audit_scope: all
      layers: ["L2", "L4"]
      severity_threshold: medium
      include_cost_analysis: true
    timeout: 10m
    
  - job: compliance_audit
    skill: audit_compliance
    params:
      frameworks: ["soc2", "gdpr"]
      audit_scope: full
      collect_evidence: true
      include_drift_detection: true
    timeout: 15m
    
  - job: performance_audit
    skill: audit_performance
    params:
      audit_scope: all
      check_slo_compliance: true
      slo_lookback_days: 7
      detect_regressions: true
    timeout: 20m
    
  - job: infrastructure_audit
    skill: audit_infrastructure
    params:
      audit_scope: all
      environments: ["staging", "production"]
      run_iac_scanners: true
      drift_detection: true
    timeout: 15m
```

### Phase 2: Contract & Drift Assessment

```yaml
sequential_jobs:
  - job: contract_drift_check
    skill: assess_drift
    params:
      drift_types: ["openapi", "frontend_backend", "cross_layer"]
      layers: ["L2", "L3", "L4", "frontend"]
      severity_threshold: warning
    depends_on: []
    timeout: 10m
```

### Phase 3: Results Aggregation

Consolidate all findings into unified report:

```python
async def aggregate_audit_results(results: dict) -> dict:
    """Aggregate findings from all audit skills."""
    
    summary = {
        "audit_date": datetime.utcnow().isoformat(),
        "trigger": results.trigger_reason,
        "overall_readiness": "unknown",
        "critical_blockers": [],
        "high_priority": [],
        "total_findings": 0,
        "skills_executed": [],
    }
    
    # Aggregate severity counts
    severity_totals = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    
    for skill_name, skill_result in results.items():
        if skill_result.status == "success":
            summary["skills_executed"].append(skill_name)
            
            # Count findings by severity
            summary["total_findings"] += skill_result.summary.total_findings
            severity_totals["critical"] += skill_result.summary.critical_count
            severity_totals["high"] += skill_result.summary.high_count
            severity_totals["medium"] += skill_result.summary.medium_count
            severity_totals["low"] += skill_result.summary.low_count
            
            # Collect blockers
            if skill_result.summary.critical_count > 0:
                summary["critical_blockers"].append({
                    "skill": skill_name,
                    "count": skill_result.summary.critical_count,
                    "top_issues": skill_result.findings[:3]
                })
    
    # Determine overall readiness
    if severity_totals["critical"] == 0 and severity_totals["high"] <= 3:
        summary["overall_readiness"] = "approved"
    elif severity_totals["critical"] == 0:
        summary["overall_readiness"] = "approved_with_caveats"
    else:
        summary["overall_readiness"] = "blocked"
    
    summary["severity_totals"] = severity_totals
    return summary
```

## Decision Matrix

| Critical | High | Medium | Overall Decision |
|----------|------|--------|------------------|
| 0 | 0-3 | Any | ✅ **APPROVED** |
| 0 | 4-10 | < 20 | ⚠️ **APPROVED_WITH_CAVEATS** |
| 0 | > 10 | Any | ⏸️ **CONDITIONAL** - Requires review |
| > 0 | Any | Any | ❌ **BLOCKED** - Must resolve criticals |

## Unified Report Structure

### Executive Summary

```markdown
# Pre-Production Audit Report
**Generated:** 2026-04-18T15:45:00Z  
**Trigger:** Production deploy request #1234  
**Overall Readiness:** ✅ APPROVED

## Decision
**PROCEED TO PRODUCTION** with standard monitoring.

## Findings Summary
| Severity | Count | Skills Affected |
|----------|-------|-----------------|
| 🔴 Critical | 0 | - |
| 🟠 High | 2 | infrastructure, performance |
| 🟡 Medium | 8 | compliance, ai_systems |
| 🟢 Low | 12 | all |

## Skill Results
| Skill | Status | Grade | Key Finding |
|-------|--------|-------|-------------|
| AI Systems | ✅ Pass | B+ | No prompt injection risks |
| Compliance | ✅ Pass | A | 94% SOC 2 compliant |
| Performance | ⚠️ Warn | B | L3 latency 50% over SLO |
| Infrastructure | ⚠️ Warn | B+ | 2 high severity CVEs |
| Contract Drift | ✅ Pass | A | No breaking changes |

## Required Actions (Before Deploy)
None - all critical checks passed.

## Recommended Actions (Post-Deploy)
1. Monitor L3 graph query latency (current: 750ms, target: 500ms)
2. Schedule CVE patching for layer2-extraction within 7 days
3. Review AI cost trends after extraction workload increase
```

### Detailed Findings by Skill

```yaml
ai_systems_audit:
  status: pass
  grade: B+
  findings:
    - severity: medium
      category: model_governance
      description: Fallback model not configured for L2 extraction
      remediation: Add gpt-3.5-turbo fallback for degraded mode
    - severity: low
      category: llm_costs
      description: Cost trending up 15% week-over-week
      remediation: Review extraction batch sizes
  prompt_security_score: 100
  rag_performance_score: 87
  cost_anomaly_detected: false

compliance_audit:
  status: pass
  grade: A
  soc2_score: 94
  gdpr_score: 91
  findings:
    - severity: medium
      control: CC6.2
      description: Quarterly access reviews not automated
      frameworks: [soc2]
    - severity: low
      article: Art 30
      description: Records of processing activities need update
      frameworks: [gdpr]
  evidence_bundle: ./compliance-evidence/2026-04-18/
  drift_detected: false

performance_audit:
  status: warn
  grade: B
  slo_compliance_pct: 83
  regressions_detected: 1
  findings:
    - severity: high
      metric: L3 Query Latency p99
      current: 750ms
      target: 500ms
      error_budget_remaining_pct: 12
      recommendation: Add composite index on frequent traversal queries
  load_tests_passed: 3/3
  database_optimizations: ["Add index on entity(type, status)"]
  cache_hit_rate: 72%

infrastructure_audit:
  status: warn
  grade: B+
  findings:
    - severity: high
      category: container_security
      cve: CVE-2024-1234
      image: layer2-extraction
      package: requests
      fixed_version: 2.31.0
    - severity: high
      category: kubernetes
      cis: 5.2.6
      issue: allowPrivilegeEscalation not set to false
      resources: ["layer4-agents-*"]
  drift_detected: false
  compliance_pass_rate: 96%

contract_drift:
  status: pass
  grade: A
  drift_detected: false
  openapi_accuracy: 98%
  frontend_backend_alignment: 100%
```

## Quality Gates

### Pre-Deployment Gates (Must Pass)

```yaml
gates:
  critical_findings:
    max_count: 0
    fail_message: "Critical findings block production deployment"
    
  security_gates:
    required_jobs_passed:
      - gitleaks-scan
      - trivy-image-scan
      - dast-api-scan
      - bandit-scan
    fail_message: "Security gates must pass"
    
  contract_tests:
    required: true
    min_pass_rate: 100
    fail_message: "All contract tests must pass"
    
  slo_compliance:
    min_availability_pct: 99.5
    fail_message: "SLO compliance below threshold"
```

### Post-Deployment Monitoring

```yaml
monitoring:
  duration: 30m
  checks:
    - metric: error_rate
      threshold: 1%
    - metric: p99_latency
      threshold: 200% of baseline
    - metric: workflow_success_rate
      threshold: 95%
```

## Tool Integration

```bash
# Execute full pre-production audit
python -m layer4_agents.workflows.pre_production_audit \
  --trigger production-deploy-request \
  --deploy-request-id 1234 \
  --include-evidence

# Quick check mode (faster, skips load tests)
python -m layer4_agents.workflows.pre_production_audit \
  --mode quick \
  --skip-load-tests

# Compliance-focused audit
python -m layer4_agents.workflows.pre_production_audit \
  --focus compliance,ai_systems \
  --frameworks soc2,gdpr

# CI/CD integration (fails on critical)
python -m layer4_agents.workflows.pre_production_audit \
  --mode ci \
  --fail-on-critical \
  --output-format json
```

## GitHub Actions Integration

```yaml
# .github/workflows/pre-production-audit.yml
name: Pre-Production Audit

on:
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      deploy_request_id:
        description: 'Deployment Request ID'
        required: true

jobs:
  pre_production_audit:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Pre-Production Audit
        run: |
          python -m layer4_agents.workflows.pre_production_audit \
            --trigger production-deploy-request \
            --deploy-request-id ${{ github.event.inputs.deploy_request_id }} \
            --output-format json \
            --output-path audit-results.json
      
      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: pre-production-audit-results
          path: audit-results.json
      
      - name: Check Decision
        run: |
          DECISION=$(jq -r '.overall_readiness' audit-results.json)
          if [ "$DECISION" = "blocked" ]; then
            echo "❌ Pre-production audit BLOCKED deployment"
            exit 1
          elif [ "$DECISION" = "approved_with_caveats" ]; then
            echo "⚠️ Deployment approved with caveats - review findings"
          else
            echo "✅ Pre-production audit passed - deployment approved"
          fi
```

## Deliverables

1. **Pre_Production_Audit_Report.md** - Executive summary with decision
2. **Security_Assessment.md** - Consolidated security findings
3. **Compliance_Evidence_Bundle/** - SOC 2/GDPR evidence artifacts
4. **Performance_Analysis.json** - SLO compliance and regression data
5. **Infrastructure_Scan.sarif** - SARIF format for GitHub integration
6. **Deployment_Checklist.md** - Pre/post deploy actions

## Related Skills

- `audit_ai_systems` - AI/ML security and governance
- `audit_compliance` - SOC 2, GDPR validation
- `audit_performance` - SLOs, load testing, optimization
- `audit_infrastructure` - K8s, containers, IaC
- `assess_drift` - Contract and configuration drift
