---
name: audit_compliance
description: Automated compliance audit for SOC 2 Type II, GDPR, and ISO 27001 controls with evidence collection and drift detection. Generates auditor-ready reports with evidence bundles.
allowed_agents: ["compliance-auditor", "security-auditor", "governance-officer", "pre-production-audit"]
---

# Audit Compliance Skill

## Purpose

This skill automates compliance auditing for enterprise SaaS requirements, providing:
- SOC 2 Type II control validation with evidence collection
- GDPR data protection assessment and data flow mapping
- ISO 27001 information security management review
- Audit logging completeness verification
- Data retention policy compliance checking
- Automated evidence bundle generation for external auditors

## When to Use

- Quarterly compliance assessments (SOC 2, GDPR)
- Pre-production readiness validation
- External audit preparation (evidence collection)
- Post-incident compliance verification
- Annual compliance recertification
- After significant architectural changes affecting data handling

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| frameworks | string[] | No | ["soc2", "gdpr"] | Compliance frameworks to audit |
| controls | string[] | No | [] | Specific control IDs (empty = all) |
| collect_evidence | boolean | No | true | Collect and bundle evidence artifacts |
| evidence_retention_days | integer | No | 90 | Retention for evidence (min 30) |
| audit_scope | string | No | "full" | Scope: full, security, data_protection, access_control, monitoring, incident_response |
| include_drift_detection | boolean | No | true | Detect drift from previous baseline |
| severity_threshold | string | No | "medium" | Minimum severity: critical, high, medium, low |
| output_format | string | No | "markdown" | Output: markdown, json, pdf, sarif |
| output_directory | string | No | "./compliance-evidence" | Evidence artifact directory |
| fail_on_critical | boolean | No | true | Fail if critical findings detected |

## Audit Steps

### 1. SOC 2 Type II Control Validation

Map and validate Trust Service Criteria:

**Common Criteria (CC):**

| Control | Implementation Evidence | Validation Method |
|---------|--------------------------|-------------------|
| CC6.1 - Logical Access | RBAC in `shared/identity/`, OIDC routes | Review route guards, test permission matrix |
| CC6.2 - Access Removal | `user.deactivated` audit events | Query audit log for deactivation events |
| CC6.3 - Access Credentials | API key rotation, JWT expiration | Check `API_KEY_REVOKED` events, token TTL |
| CC7.1 - Security Operations | Security gates workflow | Review `.github/workflows/security-gates.yml` |
| CC7.2 - Vulnerability Management | Trivy, Bandit, Semgrep scans | Check scan results, SBOM generation |
| CC8.1 - Change Management | PR reviews, deployment runbooks | Git history, `deployment-rollout-and-rollback.md` |

**Availability (A):**
- A1.1: Monitoring with Prometheus/Grafana (evidence: dashboards, alerts)
- A1.2: Incident response runbooks (evidence: `docs/runbooks/`)
- A1.3: Backup and recovery testing (evidence: `backup-disaster-recovery.md`)

**Processing Integrity (PI):**
- PI1.3: Data validation (evidence: Pydantic models, input validation)
- PI1.4: Error handling (evidence: error response standardization)

**Confidentiality (C):**
- C1.1: Encryption in transit (evidence: TLS configuration)
- C1.2: Encryption at rest (evidence: database encryption, secret management)

### 2. GDPR Data Protection Assessment

Map data flows and verify protection measures:

```python
# Data inventory validation
DATA_CATEGORIES = {
    "personal_data": [
        "user.email", "user.name", "tenant.billing_contact",
        "extracted_content.pii_detected"
    ],
    "sensitive_data": [
        "api_key.hashed_value", "oauth.tokens",
        "audit_events.ip_address"
    ],
    "system_data": [
        "metrics", "logs", "traces"
    ]
}

# Verify processing activities
PROCESSING_ACTIVITIES = {
    "ingestion": {
        "purpose": "Content extraction and analysis",
        "lawful_basis": "Legitimate interest (contract execution)",
        "retention_days": 90,
        "automated": True
    },
    "audit_logging": {
        "purpose": "Security and compliance monitoring",
        "lawful_basis": "Legal obligation (SOC 2)",
        "retention_days": 2555,  # 7 years
        "automated": True
    }
}
```

**GDPR Article Mapping:**

| Article | Requirement | Implementation | Evidence |
|---------|-------------|----------------|----------|
| Art 5 | Data minimization | PII redaction in L1 | `PIIScanner` implementation |
| Art 17 | Right to erasure | `cleanup_old_content` task | Celery task definition |
| Art 25 | Privacy by design | Encryption at rest/transit | K8s configs, TLS settings |
| Art 30 | Records of processing | Data inventory documentation | This audit output |
| Art 32 | Security of processing | RBAC, encryption, access logs | `shared/audit/` module |
| Art 33 | Breach notification | Incident response runbooks | `incident-postmortem-template.md` |

### 3. Audit Logging Verification

Validate comprehensive audit trail coverage:

```python
REQUIRED_AUDIT_EVENTS = {
    # Authentication/Authorization
    "user.login", "user.login_failed", "user.activated", "user.deactivated",
    "api_key.created", "api_key.revoked", "api_key.used",
    "tenant.created", "tenant.suspended", "tenant.deleted",
    
    # Data Lifecycle
    "document.ingested", "extraction.run", "kg.node_created",
    "kg.node_updated", "kg.node_deleted",
    
    # Administrative
    "workflow.started", "workflow.completed", "workflow.failed",
    "feature_flag.updated", "model.registered"
}

# Verify each event type has been logged in past 90 days
```

**Audit Log Requirements:**
- [ ] All authentication events logged
- [ ] All data modification events logged
- [ ] Administrative actions logged
- [ ] System configuration changes logged
- [ ] 7-year retention for compliance events
- [ ] Tamper-proof storage (append-only)
- [ ] Structured JSON format for analysis
- [ ] Correlation IDs for request tracing

### 4. Data Retention Compliance

Verify retention policies are enforced:

```python
RETENTION_POLICIES = {
    "raw_content": {"days": 90, "automated": True, "task": "cleanup_old_content"},
    "extracted_data": {"days": 365, "automated": False, "review_required": True},
    "audit_events": {"days": 2555, "automated": False, "legal_hold_capable": True},
    "session_logs": {"days": 30, "automated": True, "task": "log_rotation"},
    "metrics": {"days": 90, "automated": True, "aggregation": "after_90d"}
}

# Validate each policy has:
# - Defined retention period
# - Automated deletion OR documented review process
# - Legal hold capability for litigation
```

### 5. Access Control Assessment

Review RBAC and access management:

```python
ACCESS_CONTROL_CHECKS = {
    "tenant_isolation": {
        "implemented": True,
        "evidence": ["tests/security/test_tenant_isolation.py"],
        "gaps": []
    },
    "rbac_enforcement": {
        "implemented": True,
        "evidence": ["shared/identity/rbac.py", "RouteGuard.tsx"],
        "gaps": []
    },
    "mfa": {
        "implemented": True,  # Via OIDC provider
        "evidence": ["OIDC configuration"],
        "gaps": ["Direct API key access lacks MFA"]
    },
    "access_reviews": {
        "implemented": False,
        "evidence": [],
        "gaps": ["No quarterly access review process"]
    }
}
```

## Evidence Collection

### Artifact Types

For each control, collect:
1. **Code Evidence** - Implementation files, configuration
2. **Test Evidence** - Passing test results, coverage reports
3. **Log Evidence** - Sample audit events (sanitized)
4. **Process Evidence** - Runbooks, procedures, workflows
5. **Config Evidence** - Security policies, retention settings

### Evidence Bundle Structure

```
compliance-evidence/
├── manifest.json                    # Index of all evidence
├── soc2/
│   ├── cc6.1-logical-access/
│   │   ├── rbac-implementation.zip
│   │   ├── permission-matrix-test-results.json
│   │   └── route-guard-code-review.md
│   └── cc7.1-security-ops/
│       ├── security-gates-workflow.yml
│       └── scan-results/
├── gdpr/
│   ├── art25-privacy-by-design/
│   │   ├── encryption-config.yml
│   │   └── data-flow-diagram.pdf
│   └── art32-security/
│       ├── access-control-matrix.xlsx
│       └── breach-response-runbook.pdf
└── iso27001/
    └── a12.4-logging/
        └── audit-log-architecture.md
```

## Drift Detection

Compare current state against baseline:

```python
# Load previous compliance baseline
previous_baseline = load_baseline("compliance-baseline.json")

# Detect changes
drift_detected = False
drift_details = []

for control_id in current_controls:
    prev_status = previous_baseline.get(control_id, {}).get("status")
    curr_status = current_controls[control_id].status
    
    if prev_status == "compliant" and curr_status != "compliant":
        drift_detected = True
        drift_details.append({
            "control_id": control_id,
            "change_type": "regression",
            "previous_status": prev_status,
            "current_status": curr_status
        })
```

## Output Structure

### Executive Summary

```markdown
## Compliance Posture: ACCEPTABLE

**Overall Score:** 87/100

**SOC 2:** 42/45 controls compliant (93%)
**GDPR:** 28/32 requirements met (88%)

**Key Strengths:**
- Comprehensive audit logging infrastructure
- Strong tenant isolation controls
- Automated security scanning in CI/CD

**Priority Gaps:**
- Quarterly access reviews not implemented (SOC 2 CC6.2)
- Automated data retention only for raw content (GDPR Art 5)
- Model governance documentation incomplete

**Recommended Actions:**
1. Implement quarterly access review process (30 days)
2. Extend automated retention to all data categories (60 days)
3. Complete model registry documentation (14 days)
```

### Control Details

```json
{
  "control_id": "CC6.1",
  "control_name": "Logical Access Security",
  "trust_service_criteria": "Security",
  "status": "compliant",
  "severity": "n/a",
  "findings": [],
  "evidence": [
    "shared/identity/rbac.py - RBAC implementation",
    "tests/security/test_rbac.py - 15 passing tests",
    "frontend/src/components/RouteGuard.tsx - UI enforcement"
  ],
  "recommendations": [],
  "owner": "Security Team",
  "remediation_timeline": "n/a"
}
```

## Example Usage

```bash
# Full compliance audit
python -m layer4_agents.tools.audit_compliance --frameworks soc2,gdpr

# SOC 2 only with evidence collection
python -m layer4_agents.tools.audit_compliance --frameworks soc2 --collect-evidence --evidence-retention-days 180

# GDPR data protection focus
python -m layer4_agents.tools.audit_compliance --frameworks gdpr --audit-scope data_protection

# CI gate mode
python -m layer4_agents.tools.audit_compliance --fail-on-critical --output-format json

# Drift detection from previous baseline
python -m layer4_agents.tools.audit_compliance --include-drift-detection --output-directory ./compliance-drift
```

## Integration with Pre-Production Audit

This skill is automatically invoked by the `pre-production-audit` workflow when:
- Production deployment is requested
- Compliance-related files change (controls matrix, policies)
- Quarterly audit schedule triggers
- SOC 2 or GDPR recertification is due

## Related Skills

- `audit_ai_systems` - AI/ML-specific compliance (model governance)
- `assess_drift` - Detect configuration drift affecting compliance
- `generate_business_case` - Create compliance investment proposals

## References

- `docs/compliance/control-matrix.md` - SOC 2 control mapping
- `shared/audit/` - Audit logging implementation
- `docs/runbooks/` - Incident response procedures
- `tests/security/` - Security control tests
