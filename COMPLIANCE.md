# Compliance Controls Mapping

## Overview

This document maps Value Fabric platform controls to SOC 2 Type II and ISO 27001:2022 requirements.

## SOC 2 Trust Services Criteria

### CC6.1 - Logical Access Security

| Control | Implementation | Evidence Location |
|---------|---------------|-------------------|
| **CC6.1.1** | Unique user IDs | `shared/identity/jwt_middleware.py` |
| **CC6.1.2** | Strong authentication | OIDC integration, MFA support in IdP |
| **CC6.1.3** | Role-based access | RBAC in `shared/identity/rbac.py` |
| **CC6.1.4** | Least privilege | Service accounts with minimal permissions |
| **CC6.1.5** | Access reviews | Quarterly access audits via `scripts/access_review.py` |

### CC6.2 - Access Removal

| Control | Implementation | Evidence Location |
|---------|---------------|-------------------|
| **CC6.2.1** | Timely removal | Offboarding checklist in `docs/operations/` |
| **CC6.2.2** | Automated revocation | Token blacklisting via Redis |

### CC6.3 - Access Control Changes

| Control | Implementation | Evidence Location |
|---------|---------------|-------------------|
| **CC6.3.1** | Change authorization | CODEOWNERS, PR approval required |
| **CC6.3.2** | Change logging | Audit logs in `layer5-ground-truth/` |

### CC6.4 - Logical Access Monitoring

| Control | Implementation | Evidence Location |
|---------|---------------|-------------------|
| **CC6.4.1** | Failed access logging | `shared/audit/logger.py` |
| **CC6.4.2** | Suspicious activity alerts | Prometheus alerts in `monitoring/alerting/` |

### CC7.1 - Security Operations

| Control | Implementation | Evidence Location |
|---------|---------------|-------------------|
| **CC7.1.1** | Threat detection | SecurityMiddleware, WAF rules |
| **CC7.1.2** | Vulnerability scanning | Trivy/Grype in CI |
| **CC7.1.3** | Patch management | Dependabot, Renovate PRs |

### CC7.2 - Security Incident Detection

| Control | Implementation | Evidence Location |
|---------|---------------|-------------------|
| **CC7.2.1** | Incident detection | PagerDuty integration |
| **CC7.2.2** | Incident response | `RUNBOOK.md` |
| **CC7.2.3** | Incident documentation | Post-incident reviews in `docs/incidents/` |

## ISO 27001:2022 Annex A Controls

### A.5 - Organizational Controls

| Control | Title | Implementation |
|---------|-------|----------------|
| **A.5.1** | Policies for info security | `SECURITY.md`, `AGENTS.md` |
| **A.5.2** | Information security roles | CODEOWNERS, team structure |
| **A.5.7** | Threat intelligence | THREAT_MODEL.md, security scanning |

### A.6 - People Controls

| Control | Title | Implementation |
|---------|-------|----------------|
| **A.6.1** | Screening | HR process (external) |
| **A.6.2** | Terms of employment | Security clauses in contracts |
| **A.6.3** | Information security awareness | Security training, `SECURITY.md` |

### A.7 - Physical Controls

| Control | Title | Implementation |
|---------|-------|----------------|
| **A.7.1** | Physical security perimeters | Cloud provider (AWS/GCP/Azure) |
| **A.7.2** | Physical entry controls | Cloud provider |

### A.8 - Technological Controls

| Control | Title | Implementation |
|---------|-------|----------------|
| **A.8.1** | User endpoint devices | BYOD policy, MDM (external) |

### A.9 - Access Controls

| Control | Title | Implementation |
|---------|-------|----------------|
| **A.9.1** | Access to networks | NetworkPolicies, VPN required |
| **A.9.2** | Access to systems | RBAC, JWT validation |
| **A.9.3** | Access to apps | OIDC, role-based permissions |
| **A.9.4** | System access control | `shared/identity/` |
| **A.9.5** | Secure log-on | OIDC with strong authentication |
| **A.9.6** | Privilege management | Least-privilege IAM |
| **A.9.7** | Access to source code | CODEOWNERS, branch protection |

### A.10 - Cryptography

| Control | Title | Implementation |
|---------|-------|----------------|
| **A.10.1** | Cryptographic controls | TLS 1.3, AES-256, HMAC-SHA256 |

### A.12 - Operations Security

| Control | Title | Implementation |
|---------|-------|----------------|
| **A.12.1** | Operational procedures | `RUNBOOK.md` |
| **A.12.2** | Protection from malware | Container scanning, no package managers in runtime |
| **A.12.3** | Backup | Database backups, point-in-time recovery |
| **A.12.4** | Logging and monitoring | Structured logs, audit trail |
| **A.12.5** | Control of operational software | GitOps, immutable infrastructure |
| **A.12.6** | Technical vulnerability management | Dependency scanning, patch policy |
| **A.12.7** | Protection of system test data | Synthetic data for tests, no production data |

### A.13 - Communications Security

| Control | Title | Implementation |
|---------|-------|----------------|
| **A.13.1** | Network security management | NetworkPolicies, mTLS |
| **A.13.2** | Information transfer | TLS 1.3, encryption in transit |

### A.14 - System Acquisition and Maintenance

| Control | Title | Implementation |
|---------|-------|----------------|
| **A.14.1** | Security requirements | Security in SDLC, threat modeling |
| **A.14.2** | Security in development | SAST/SCA in CI, code review required |
| **A.14.3** | Test data | Synthetic data, data masking |
| **A.14.9** | System acceptance testing | Staging environment, smoke tests |

### A.15 - Supplier Relationships

| Control | Title | Implementation |
|---------|-------|----------------|
| **A.15.1** | Information security policy for supplier | Vendor security assessments |
| **A.15.2** | Addressing security within supplier agreements | Cloud provider contracts |

### A.16 - Incident Management

| Control | Title | Implementation |
|---------|-------|----------------|
| **A.16.1** | Responsibilities and procedures | `RUNBOOK.md` |
| **A.16.2** | Incident reporting | PagerDuty, Slack integration |
| **A.16.3** | Assessment and decision | Incident severity matrix |
| **A.16.4** | Evidence collection | Audit logs, immutable storage |

### A.17 - Business Continuity

| Control | Title | Implementation |
|---------|-------|----------------|
| **A.17.1** | Planning | DR policy in `docs/reliability/dr-policy.md` |
| **A.17.2** | Redundancy | Multi-zone deployment, auto-failover |

### A.18 - Compliance

| Control | Title | Implementation |
|---------|-------|----------------|
| **A.18.1** | Identification of statutory requirements | Legal review, compliance register |
| **A.18.2** | Intellectual property rights | License compliance (FOSSA/Black Duck) |

## Control Evidence Collection

### Automated Evidence

| Evidence Type | Collection Method | Storage Location |
|--------------|-------------------|-------------------|
| Security scan results | CI pipeline | GitHub Security tab |
| Access logs | Application middleware | PostgreSQL audit table |
| Change history | Git repository | GitHub (signed commits) |
| Test results | CI pipeline | GitHub Actions artifacts |
| Deployment records | GitOps controller | Argo CD history |

### Manual Evidence

| Evidence Type | Frequency | Owner |
|--------------|-----------|-------|
| Access reviews | Quarterly | Security Lead |
| Penetration test | Annual | External vendor |
| Policy review | Annual | Compliance Officer |
| Incident response drill | Semi-annual | Incident Commander |
| Disaster recovery test | Annual | SRE Lead |

## Audit Trail Requirements

All audit logs must include:
- Timestamp (UTC, millisecond precision)
- Actor (user ID, service account)
- Action (CRUD operation)
- Resource (tenant, entity, record ID)
- Result (success/failure)
- Source IP
- Trace ID (for request correlation)

Storage:
- Retention: 7 years (compliance requirement)
- Immutability: Append-only, trigger-enforced
- Encryption: AES-256 at rest
- Access: Security team only

## Compliance Monitoring

### Continuous Controls Monitoring

Automated checks run daily:
- Access control violations
- Unpatched critical vulnerabilities
- Failed backups
- Drift from approved configurations
- Expired certificates

### Quarterly Reviews

- Access permissions (user and service accounts)
- Security policy effectiveness
- Incident response readiness
- Third-party risk assessment

## Certification Roadmap

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| SOC 2 Type I | Q3 2026 | 🔄 In Progress |
| SOC 2 Type II | Q1 2027 | 📋 Planned |
| ISO 27001 | Q2 2027 | 📋 Planned |
| GDPR compliance | ✅ Achieved | ✅ Complete |

---

**Last Updated**: 2026-04-15  
**Version**: 1.0.0  
**Owner**: Compliance Engineering  
**Next Review**: 2026-07-15
