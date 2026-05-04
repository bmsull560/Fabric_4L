# **VALUE FABRIC: OPERATIONS & GOVERNANCE RULES** (Full Reference)

**Status:** Legacy Reference Material
**Last Reviewed:** 2026-05-04
**Note:** This document provides a full reference for operations and governance rules. For current rule enforcement, see the YAML rule files in this directory (`hard-constraints.yaml`, `safety-rules.yaml`, `dependency-rules.yaml`, `style-rules.yaml`).

## **1. DATA GOVERNANCE & QUALITY**

### **Data Classification**
| Level | Definition | Handling |
|-------|------------|----------|
| **Public** | Scraped from public websites | Standard encryption |
| **Internal** | Proprietary ontology, formulas | Encryption at rest, audit logs |
| **Confidential** | Customer ROI calculations | Field-level encryption |
| **Restricted** | PII, audit trails | Tokenization, 90-day retention max |

### **Data Quality Rules**
1. **Provenance**: Every data point traces to source (URL + timestamp)
2. **Confidence scoring**: All LLM outputs include 0.0-1.0 confidence
3. **Schema validation**: Zero tolerance for violations in production
4. **Deduplication**: Entity resolution before persistence
5. **Freshness**: Content >90 days flagged for re-crawl

### **Retention Policies**
- Raw HTML: 30 days (purge, keep Markdown)
- Extracted entities: Indefinite (versioned)
- Audit logs: 7 years (compliance)
- Agent conversations: 1 year
- Failed job logs: 90 days

---

## **2. SECURITY & COMPLIANCE**

### **Mandatory Security Controls**
- [ ] All services authenticate via mTLS or JWT
- [ ] Secrets in AWS Secrets Manager / HashiCorp Vault (never in code)
- [ ] SQL/Cypher injection prevention: parameterized queries only
- [ ] XSS protection: sanitize all user inputs
- [ ] Rate limiting: 1000 req/min per API key
- [ ] Dependency scanning: Snyk or Dependabot (weekly)
- [ ] Container scanning: Trivy on all images
- [ ] No production data in non-prod (synthetic only)

### **Compliance**
- **GDPR**: Right to deletion, data portability APIs
- **CCPA**: Do Not Sell (implement for B2B)
- **SOC 2 Type II**: Audit trails, quarterly access reviews
- **robots.txt**: 100% compliance (P0 bug if violated)

### **PII Handling**
- **Detection**: Microsoft Presidio on all ingested content
- **Redaction**: Automatic, irreversible
- **Blocking**: Pages with >3 PII entities rejected
- **Logging**: Hash of redacted content only

---

## **3. OBSERVABILITY & MONITORING**

### **Three Pillars**
| Pillar | Implementation |
|--------|----------------|
| **Metrics** | Prometheus + Grafana, 15s scrape |
| **Logs** | Structured JSON, centralized |
| **Traces** | OpenTelemetry, 100% sampling for agents |

### **Required Metrics**
```
# System Health
- request_latency_seconds (p50, p95, p99)
- error_rate (by endpoint, by error type)
- throughput (requests/minute)

# Business Logic
- entities_extracted_per_hour
- graph_query_latency
- agent_workflow_success_rate
- roi_calculation_accuracy

# Data Quality
- schema_validation_failure_rate
- deduplication_merge_rate
- confidence_score_distribution
```

### **Alerting Rules (PagerDuty)**
| Severity | Condition | Response |
|----------|-----------|----------|
| **P0** | Ingestion down >5min, security breach | Page immediately |
| **P1** | Extraction backlog >10k, graph queries >2s | Page business hours |
| **P2** | Confidence dropping, cache hit <80% | Slack + ticket |
| **P3** | Disk >80%, non-critical failures | Email, weekly review |

### **SLIs & SLOs**
| Service | SLI | SLO | Error Budget |
|---------|-----|-----|--------------|
| Ingestion API | Availability | 99.9% | 43m/month |
| Graph Queries | Latency p95 | <500ms | 5% over |
| Extraction | Success Rate | 99.5% | 0.5% failures |
| Agent Workflows | Completion | 99% | 1% dropped |

---

## **4. DEPLOYMENT & INFRASTRUCTURE**

### **Environment Strategy**
| Environment | Purpose | Data | Access |
|-------------|---------|------|--------|
| **local** | Dev testing | Synthetic | Developer |
| **dev** | Feature testing | Synthetic | Team |
| **staging** | Integration testing | Anonymized sample | Team + QA |
| **prod** | Live system | Production | SRE only |

### **Infrastructure as Code**
- **Terraform**: All AWS/GCP resources
- **Helm**: All Kubernetes deployments
- **Policy**: No manual console changes (detected = alert)

### **Container Standards**
```dockerfile
FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
USER 1000:1000
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
WORKDIR /app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

### **Deployment Rules**
- **Blue/Green**: Zero-downtime deployments
- **Canary**: 5% → 25% → 100% traffic shift
- **Rollback**: Auto on error rate >1% or latency >200%
- **DB migrations**: Backward compatible, run before app deployment

---

## **5. INCIDENT RESPONSE**

### **Severity Levels**
| Level | Definition | Response | Communication |
|-------|------------|----------|---------------|
| **SEV-1** | Complete outage, data loss | 15 min | War room + exec |
| **SEV-2** | Major feature degraded | 1 hour | Slack + status page |
| **SEV-3** | Minor issue, workaround exists | 4 hours | Ticket + standup |
| **SEV-4** | Cosmetic, no user impact | 1 week | Backlog |

### **Incident Process**
1. **Detect**: Monitoring alert or manual report
2. **Triage**: Assign severity, create incident channel
3. **Mitigate**: Stop the bleeding (rollback, scale, etc.)
4. **Resolve**: Fix root cause
5. **Post-Mortem**: Within 48 hours for SEV-1/2

---

## **6. PERFORMANCE BUDGETS**

| Layer | Metric | Budget | Enforcement |
|-------|--------|--------|-------------|
| Layer 1 | Crawl throughput | 1000 pages/hour/worker | Auto-scale |
| Layer 2 | Extraction latency | <30s per document | Alert >20s |
| Layer 3 | Query p95 latency | <500ms multi-hop | Circuit breaker |
| Layer 4 | Workflow completion | <5 min end-to-end | Timeout + alert |
| All | Memory per pod | <2GB | OOMKill prevention |
| All | CPU per pod | <1 core average | Throttling alert |

---

## **7. REVIEW & EVOLUTION**

### **Monthly Reviews**
- Architecture review: Still aligned with goals?
- Tech debt review: Prioritize refactoring
- Security review: New threats, patches needed
- Cost review: Optimize spend

### **Quarterly Goals**
- OKRs defined at project level
- Each layer has measurable KRs
- Demo day: Show progress to stakeholders

### **Annual Audit**
- External security penetration test
- Compliance audit (SOC 2)
- Architecture fitness review
- Technology refresh evaluation

---

**See `rules.md` for Code Quality, Testing, API Design, Documentation, and AI/LLM Governance.**

**Enforcement**: These rules are checked in CI/CD. Violations block merge.
