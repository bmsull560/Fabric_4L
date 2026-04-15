# Threat Model - Value Fabric Platform

## Overview

This document describes security threats to the Value Fabric platform using STRIDE and LINDDUN methodologies, along with implemented mitigations.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USERS                                 │
│         (Tenants, Admin, Developers, Agents)                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                     FRONTEND                                 │
│              (React + Vite + OIDC Auth)                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   API GATEWAY                                │
│         (Rate Limiting, Auth, Routing, WAF)                 │
└───────┬───────┬───────┼───────┬───────┬─────────────────────┘
        │       │       │       │       │
   ┌────▼───┐ ┌─▼────┐ ┌▼───┐ ┌─▼───┐ ┌─▼────┐
   │ Layer1 │ │Layer2│ │L3  │ │L4   │ │L5/L6 │
   │Ingest  │ │Extract│ │Know│ │Agents│ │Ground│
   │(Redis) │ │(LLM)  │ │Graph│ │(LangGraph)│ │Truth │
   └────────┘ └──────┘ └────┘ └─────┘ └──────┘
        │       │       │       │       │
        └───────┴───────┴───────┴───────┘
                        │
              ┌─────────▼─────────┐
              │   DATA STORES     │
              │ (PostgreSQL +   │
              │  Neo4j + Redis)  │
              └───────────────────┘
```

## STRIDE Analysis

### S - Spoofing (Identity)

| Threat | Description | Mitigation | Status |
|--------|-------------|------------|--------|
| **T1.1** | Attacker spoofs OIDC identity | JWT validation with JWKS, short TTL (15 min) | ✅ Implemented |
| **T1.2** | Attacker steals session token | HttpOnly cookies, CSRF protection, token rotation | ✅ Implemented |
| **T1.3** | Attacker impersonates service | mTLS between services, service account tokens | ⚠️ Partial (K8s only) |
| **T1.4** | Attacker forges webhook calls | HMAC-SHA256 signatures, timestamp validation | ✅ Implemented |

### T - Tampering

| Threat | Description | Mitigation | Status |
|--------|-------------|------------|--------|
| **T2.1** | Request/response tampering in transit | TLS 1.3 everywhere, certificate pinning | ✅ Implemented |
| **T2.2** | Data tampering at rest | AES-256 encryption, database-level encryption | ✅ Implemented |
| **T2.3** | Audit log tampering | Append-only logs, DB trigger enforcement, WORM storage | ✅ Implemented |
| **T2.4** | Build artifact tampering | Signed containers (Cosign), SBOM verification | 🔄 In Progress |
| **T2.5** | Configuration tampering | GitOps, drift detection, signed configs | 🔄 In Progress |

### R - Repudiation

| Threat | Description | Mitigation | Status |
|--------|-------------|------------|--------|
| **T3.1** | User denies action | Immutable audit logs with user ID, timestamp, IP | ✅ Implemented |
| **T3.2** | Admin denies configuration change | Git commit history, signed commits, CODEOWNERS | ✅ Implemented |
| **T3.3** | System denies processing | Structured logging with trace IDs, request correlation | ✅ Implemented |

### I - Information Disclosure

| Threat | Description | Mitigation | Status |
|--------|-------------|------------|--------|
| **T4.1** | Sensitive data in logs | PII classification, redaction at source, log filtering | ✅ Implemented |
| **T4.2** | Error messages leak internals | Generic error messages, detailed logs internal only | ✅ Implemented |
| **T4.3** | Tenant data leakage | Row-level security, tenant ID validation on every query | ✅ Implemented |
| **T4.4** | Secrets in repository | Gitleaks pre-commit, CI secrets scanning | ✅ Implemented |
| **T4.5** | Cache side-channel | Cache isolation by tenant, constant-time comparisons | ⚠️ Partial |

### D - Denial of Service

| Threat | Description | Mitigation | Status |
|--------|-------------|------------|--------|
| **T5.1** | API rate limit abuse | Tiered rate limits (auth: 5/min, API: 100/min) | ✅ Implemented |
| **T5.2** | Resource exhaustion | Resource quotas, autoscaling, circuit breakers | ✅ Implemented |
| **T5.3** | Graph query complexity | Query depth limits, timeout enforcement, cost analysis | ✅ Implemented |
| **T5.4** | LLM token flooding | Token budget per request, concurrent request limits | ✅ Implemented |
| **T5.5** | Large payload attacks | Request size limits (10MB), streaming for large data | ✅ Implemented |

### E - Elevation of Privilege

| Threat | Description | Mitigation | Status |
|--------|-------------|------------|--------|
| **T6.1** | Horizontal privilege escalation | Tenant isolation middleware, row-level security | ✅ Implemented |
| **T6.2** | Vertical privilege escalation | RBAC enforcement, role validation on every endpoint | ✅ Implemented |
| **T6.3** | Service account abuse | Least-privilege IAM, workload identity, short-lived tokens | ⚠️ Partial |
| **T6.4** | Container escape | Distroless images, non-root user, restricted capabilities | 🔄 In Progress |

## LINDDUN Analysis (Privacy)

### Linkability

| Threat | Description | Mitigation | Status |
|--------|-------------|------------|--------|
| **P1.1** | User actions linked across sessions | Session ID rotation, anonymized analytics | ✅ Implemented |
| **P1.2** | Tenant data linked in logs | Tenant-specific log streams, log sanitization | ✅ Implemented |

### Identifiability

| Threat | Description | Mitigation | Status |
|--------|-------------|------------|--------|
| **P2.1** | PII in request logs | PII detection, redaction, classification tags | ✅ Implemented |
| **P2.2** | User identifiable via graph patterns | Differential privacy for analytics queries | ⚠️ Planned |

### Non-repudiation (Privacy context)

| Threat | Description | Mitigation | Status |
|--------|-------------|------------|--------|
| **P3.1** | User cannot prove data deletion | Deletion receipts, audit trail of data lifecycle | ✅ Implemented |

### Detectability

| Threat | Description | Mitigation | Status |
|--------|-------------|------------|--------|
| **P4.1** | Presence of sensitive data fields | Field-level encryption, access logging | ✅ Implemented |

### Disclosure of Information

Covered in STRIDE Information Disclosure (T4.x)

### Unawareness

| Threat | Description | Mitigation | Status |
|--------|-------------|------------|--------|
| **P6.1** | Users unaware of data processing | Privacy policy, consent management, data inventory | ⚠️ Partial |
| **P6.2** | Admin unaware of security events | Security dashboards, alerting, audit summaries | ✅ Implemented |

### Non-compliance

| Threat | Description | Mitigation | Status |
|--------|-------------|------------|--------|
| **P7.1** | GDPR data retention violations | Automated data retention policies, deletion workflows | ✅ Implemented |
| **P7.2** | SOC2 control gaps | Control mapping, continuous monitoring, evidence bundles | 🔄 In Progress |

## Attack Scenarios

### Scenario 1: Cross-Tenant Data Access

**Attacker**: Tenant A user tries to access Tenant B data
**Vector**: Modified request with spoofed tenant ID header
**Mitigation**: 
1. JWT contains tenant claim (immutable)
2. Every query includes `WHERE tenant_id = :jwt_tenant_id`
3. RLS policies enforced at database level
**Test**: `tests/security/test_tenant_isolation.py`

### Scenario 2: Privilege Escalation

**Attacker**: Standard user tries admin operations
**Vector**: Modified JWT role claim, or direct API call to admin endpoints
**Mitigation**:
1. RBAC middleware validates role on every request
2. Admin endpoints require `role=admin` in JWT
3. Role changes require re-authentication
**Test**: `tests/security/test_rbac.py`

### Scenario 3: Injection Attacks

**Attacker**: SQL/NoSQL/XSS injection via input fields
**Vector**: Malicious input in graph queries or entity creation
**Mitigation**:
1. SecurityMiddleware with pattern detection
2. Parameterized queries only
3. Input sanitization, HTML escaping
4. RDF/Turtle paths bypass validation (legitimate)
**Test**: `tests/security/test_injection.py`

### Scenario 4: Supply Chain Poisoning

**Attacker**: Compromised dependency or build process
**Vector**: Malicious package version, tampered container
**Mitigation**:
1. Pinned dependencies (lockfiles)
2. Signed containers (Cosign)
3. SBOM verification
4. Admission controller blocks unsigned images
**Test**: `tests/security/test_supply_chain.py`

### Scenario 5: Insider Threat

**Attacker**: Malicious developer or compromised account
**Vector**: Direct database access, privilege abuse
**Mitigation**:
1. Least-privilege access (no direct prod DB access)
2. Audit logging of all data access
3. CODEOWNERS for sensitive changes
4. Segregation of duties (deploy ≠ code)
**Test**: `tests/security/test_insider_threat.py`

## Risk Ratings

| Threat | Likelihood | Impact | Risk | Priority |
|--------|-----------|--------|------|----------|
| T1.1 Identity spoofing | Medium | High | 🔴 Critical | P0 |
| T2.1 Transit tampering | Low | High | 🟡 High | P1 |
| T3.1 Action repudiation | Low | Medium | 🟢 Medium | P2 |
| T4.3 Tenant data leak | Medium | Critical | 🔴 Critical | P0 |
| T5.1 DoS via rate abuse | High | Medium | 🟡 High | P1 |
| T6.1 Horizontal escalation | Medium | Critical | 🔴 Critical | P0 |

## Mitigation Verification

| Control | Test Location | Frequency |
|---------|--------------|-----------|
| JWT validation | `tests/unit/auth/` | Every PR |
| Tenant isolation | `tests/security/test_tenant_isolation.py` | Every PR |
| RBAC enforcement | `tests/security/test_rbac.py` | Every PR |
| Input sanitization | `tests/security/test_injection.py` | Every PR |
| Rate limiting | `tests/integration/test_rate_limit.py` | Every PR |
| Container signing | `.github/workflows/security-gates.yml` | Every build |

## Threat Model Maintenance

- **Review**: Quarterly or after major architecture changes
- **Update**: After security incidents or new threat intelligence
- **Owner**: Security Engineering Lead
- **Distribution**: All engineers, security team, auditors

---

**Last Updated**: 2026-04-15  
**Version**: 1.0.0  
**Classification**: Internal
