Also, here are rules: Here are comprehensive **Global Rules** for the Value Fabric project — apply these across all 4 layers:

---

# **VALUE FABRIC: GLOBAL PROJECT RULES**

## **1. CODE QUALITY & STANDARDS**

### **Language & Framework Standards**
| Aspect | Rule |
|--------|------|
| **Python** | 3.11+ required, use async/await for I/O, type hints mandatory (mypy strict) |
| **TypeScript** | Strict mode enabled, no any types, explicit return types on exports |
| **Documentation** | Every public function has Google-style docstrings |
| **Linting** | Ruff (Python), ESLint (TS) — zero warnings in CI |
| **Formatting** | Black (Python), Prettier (TS) — auto-format on save |
| **Imports** | Absolute imports only, grouped: stdlib → third-party → local |

### **Repository Structure**
``
value-fabric/
├── .github/           # Workflows, issue templates
├── docs/              # Architecture Decision Records (ADRs)
├── infrastructure/    # Terraform, K8s manifests
├── shared/            # Cross-layer libraries (schemas, utils)
├── layer1-ingestion/  # Owns ingestion service
├── layer2-extraction/ # Owns extraction pipeline
├── layer3-knowledge/  # Owns graph + semantic layer
├── layer4-agents/     # Owns agent workflows
└── e2e-tests/         # Cross-layer integration tests
``

### **Git Workflow**
- **Branch naming**: layer-X/feature/description or fix/layer-X/bug-description 
- **Commits**: Conventional commits (feat:, fix:, docs:, refactor:, test:)
- **PR requirements**: 
  - 2 approvals for core changes
  - All tests pass
  - Coverage doesn't decrease
  - ADR attached for architectural changes

---

## **2. DATA GOVERNANCE & QUALITY**

### **Data Classification**
| Level | Definition | Handling |
|-------|------------|----------|
| **Public** | Scraped from public websites | Standard encryption |
| **Internal** | Proprietary ontology, formulas | Encryption at rest, audit logs |
| **Confidential** | Customer ROI calculations, prospect data | Field-level encryption, access controls |
| **Restricted** | PII (if any), audit trails | Tokenization, 90-day retention max |

### **Data Quality Rules**
1. **Provenance**: Every data point traces to source (URL + timestamp)
2. **Confidence scoring**: All LLM outputs include 0.0-1.0 confidence
3. **Schema validation**: Zero tolerance for schema violations in production
4. **Deduplication**: Entity resolution runs before persistence
5. **Freshness**: Content >90 days old flagged for re-crawl

### **Retention Policies**
- Raw HTML: 30 days (then purge, keep Markdown)
- Extracted entities: Indefinite (versioned)
- Audit logs: 7 years (compliance)
- Agent conversations: 1 year
- Failed job logs: 90 days

---

## **3. SECURITY & COMPLIANCE**

### **Mandatory Security Controls**
``
□ All services authenticate via mTLS or JWT
□ Secrets in AWS Secrets Manager / HashiCorp Vault (never in code)
□ SQL/Cypher injection prevention: parameterized queries only
□ XSS protection: sanitize all user inputs
□ Rate limiting: 1000 req/min per API key
□ Dependency scanning: Snyk or Dependabot (weekly)
□ Container scanning: Trivy on all images
□ No production data in non-prod environments (synthetic data only)
`

### **Compliance Requirements**
- **GDPR**: Right to deletion, data portability APIs
- **CCPA**: Do Not Sell (irrelevant for B2B, but implement anyway)
- **SOC 2 Type II**: Audit trails, access reviews quarterly
- **robots.txt**: 100% compliance (monitored, violations = P0 bug)

### **PII Handling**
- **Detection**: Microsoft Presidio on all ingested content
- **Redaction**: Automatic, irreversible
- **Blocking**: Pages with >3 PII entities rejected
- **Logging**: Hash of redacted content (not content itself)

---

## **4. OBSERVABILITY & MONITORING**

### **Three Pillars (Mandatory)**
| Pillar | Implementation |
|--------|----------------|
| **Metrics** | Prometheus + Grafana, 15s scrape interval |
| **Logs** | Structured JSON, centralized (Datadog or ELK) |
| **Traces** | OpenTelemetry, 100% sampling for agents |

### **Required Metrics**
`
# System Health
- request_latency_seconds (p50, p95, p99)
- error_rate (by endpoint, by error type)
- throughput (requests/minute)

# Business Logic
- entities_extracted_per_hour
- graph_query_latency
- agent_workflow_success_rate
- roi_calculation_accuracy (vs ground truth)

# Data Quality
- schema_validation_failure_rate
- deduplication_merge_rate
- confidence_score_distribution
`

### **Alerting Rules (PagerDuty)**
| Severity | Condition | Response |
|----------|-----------|----------|
| **P0** | ingestion down >5min, security breach | Page on-call immediately |
| **P1** | extraction backlog >10k jobs, graph queries >2s | Page during business hours |
| **P2** | confidence scores dropping, cache hit rate <80% | Slack alert, ticket created |
| **P3** | Disk >80%, non-critical job failures | Email, weekly review |

### **SLIs & SLOs**
| Service | SLI | SLO | Error Budget |
|---------|-----|-----|--------------|
| Ingestion API | Availability | 99.9% | 43m/month |
| Graph Queries | Latency p95 | <500ms | 5% over |
| Extraction | Success Rate | 99.5% | 0.5% failures |
| Agent Workflows | Completion | 99% | 1% dropped |

---

## **5. TESTING REQUIREMENTS**

### **Test Pyramid**
`
        /\
       /  \  E2E Tests (5%)  - Full workflows
      /____\ 
     /      \ Integration (15%) - Service boundaries
    /________\
   /          \ Unit Tests (80%) - Functions, classes
  /____________\
`

### **Mandatory Test Coverage**
| Layer | Minimum Coverage | Critical Paths |
|-------|------------------|----------------|
| Layer 1 | 80% | Rate limiting, PII detection, robots.txt |
| Layer 2 | 85% | Schema validation, deduplication, RDF output |
| Layer 3 | 80% | GraphRAG retrieval, semantic queries, access control |
| Layer 4 | 75% | ROI calculation, document generation, provenance |

### **Test Types**
1. **Unit**: Fast (<100ms), isolated, mocked dependencies
2. **Integration**: Test service boundaries, use testcontainers for DBs
3. **Contract**: Pact tests between layers (consumer-driven)
4. **E2E**: Full workflows with synthetic data, run in CI nightly
5. **Load**: k6 or Locust, 10x expected peak load
6. **Chaos**: Random pod kills, network latency injection (monthly)

### **CI/CD Gates**
`
□ All unit tests pass
□ Coverage >= minimum threshold
□ Integration tests pass
□ Security scan: no CRITICAL/HIGH vulnerabilities
□ Performance regression: latency <110% of baseline
□ Linting: zero warnings
□ Type checking: mypy/pyright pass
``

---

## **6. API DESIGN STANDARDS**

### **RESTful Principles**
- **URLs**: Nouns, plural, kebab-case (/capabilities, /use-cases)
- **Methods**: GET (read), POST (create), PUT (update), DELETE (remove), PATCH (partial)
- **Status codes**: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Validation Error, 500 Internal Error
- **Content-Type**: application/json default, text/turtle for RDF

### **Response Format**
``json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "links": {
    "self": "/capabilities?page=1",
    "next": "/capabilities?page=2",
    "prev": null
  }
}
`

### **Error Format**
`json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {"field": "name", "issue": "required field missing"}
    ],
    "request_id": "req_abc123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
``

### **Versioning**
- URL-based: /v1/capabilities 
- Deprecation: 6 months notice, Sunset header
- Breaking changes = new major version

---

## **7. DOCUMENTATION STANDARDS**

### **Required Documentation**
| Document | Location | Owner | Update Frequency |
|----------|----------|-------|------------------|
| Architecture Decision Records | /docs/adrs/ | Tech Lead | Per decision |
| API Reference | OpenAPI spec | API Owner | Per release |
| Runbook | /docs/runbooks/ | SRE | Quarterly |
| Onboarding Guide | /docs/onboarding.md | Team Lead | Per hire |
| Security Policy | /docs/security.md | Security | Annually |

### **Code Documentation**
- **README**: Every service has one with: purpose, setup, testing, deployment
- **Docstrings**: All public functions (Google style)
- **Comments**: Explain "why", not "what" (code shows what)
- **TODOs**: Must include ticket number (TODO(TICKET-123): description)

### **ADRs (Architecture Decision Records)**
Template:
``markdown
# ADR-012: Use Neo4j for Knowledge Graph

## Status: Accepted

## Context
We need a graph database for multi-hop reasoning...

## Decision
Use Neo4j 5.x Enterprise...

## Consequences
+ Native graph operations, GDS library
- Licensing costs, vendor lock-in

## Alternatives Considered
- Amazon Neptune: Less mature GDS
- RDFox: Better OWL, smaller community
`

---

## **8. DEPLOYMENT & INFRASTRUCTURE**

### **Environment Strategy**
| Environment | Purpose | Data | Access |
|-------------|---------|------|--------|
| **local** | Dev testing | Synthetic | Developer |
| **dev** | Feature testing | Synthetic | Team |
| **staging** | Integration testing | Anonymized prod sample | Team + QA |
| **prod** | Live system | Production | SRE only |

### **Infrastructure as Code**
- **Terraform**: All AWS/GCP resources
- **Helm**: All Kubernetes deployments
- **Policy**: No manual console changes (detected = alert)

### **Container Standards**
`dockerfile
# Base image
FROM python:3.11-slim-bookworm

# Security
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
USER 1000:1000

# Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App
COPY . /app
WORKDIR /app
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
``

### **Deployment Rules**
- **Blue/Green**: Zero-downtime deployments
- **Canary**: 5% → 25% → 100% traffic shift
- **Rollback**: Automatic on error rate >1% or latency >200%
- **Database migrations**: Backward compatible, run before app deployment

---

## **9. AI/LLM GOVERNANCE**

### **Model Usage**
| Use Case | Model | Temperature | Max Tokens |
|----------|-------|-------------|------------|
| Entity Extraction | GPT-4o / Claude 3.5 | 0.0 | 4000 |
| Relationship Extraction | GPT-4o / Claude 3.5 | 0.0 | 4000 |
| Summarization | GPT-4o-mini | 0.3 | 2000 |
| Business Case Generation | GPT-4o | 0.7 | 8000 |
| Code Generation | Claude 3.5 Sonnet | 0.2 | 4000 |

### **LLM Safety Rules**
1. **No PII in prompts**: Pre-process all inputs with PII detector
2. **Prompt versioning**: All prompts in Git, versioned with app
3. **Output validation**: Schema validation before using LLM output
4. **Fallbacks**: Local model (Llama 3) if API unavailable
5. **Cost tracking**: Tag all API calls with workflow_id, track $/request

### **Hallucination Prevention**
- Confidence thresholds: <0.8 = flag for review
- Evidence quotes: Every claim must cite source text
- Human review: All outputs >$1M impact require approval

---

## **10. INCIDENT RESPONSE**

### **Severity Levels**
| Level | Definition | Response Time | Communication |
|-------|------------|---------------|---------------|
| **SEV-1** | Complete outage, data loss | 15 min | War room + exec notify |
| **SEV-2** | Major feature degraded | 1 hour | Team Slack + status page |
| **SEV-3** | Minor issue, workaround exists | 4 hours | Ticket + daily standup |
| **SEV-4** | Cosmetic, no user impact | 1 week | Backlog |

### **Incident Process**
1. **Detect**: Monitoring alert or manual report
2. **Triage**: Assign severity, create incident channel
3. **Mitigate**: Stop the bleeding (rollback, scale up, etc.)
4. **Resolve**: Fix root cause
5. **Post-Mortem**: Within 48 hours for SEV-1/2, include:
   - Timeline
   - Root cause (5 Whys)
   - Action items (with owners)
   - Lessons learned

---

## **11. PERFORMANCE BUDGETS**

| Layer | Metric | Budget | Enforcement |
|-------|--------|--------|-------------|
| Layer 1 | Crawl throughput | 1000 pages/hour/worker | Auto-scale |
| Layer 2 | Extraction latency | <30s per document | Alert >20s |
| Layer 3 | Query p95 latency | <500ms multi-hop | Circuit breaker |
| Layer 4 | Workflow completion | <5 min end-to-end | Timeout + alert |
| All | Memory per pod | <2GB | OOMKill prevention |
| All | CPU per pod | <1 core average | Throttling alert |

---

## **12. REVIEW & EVOLUTION**

### **Monthly Reviews**
- Architecture review: Are we still aligned with goals?
- Tech debt review: Prioritize refactoring
- Security review: New threats, patches needed
- Cost review: Optimize spend

### **Quarterly Goals**
- OKRs defined at project level
- Each layer has measurable KR
- Demo day: Show progress to stakeholders

### **Annual Audit**
- External security penetration test
- Compliance audit (SOC 2)
- Architecture fitness review
- Technology refresh evaluation

---

**Enforcement**: These rules are checked in CI/CD. Violations block merge. Questions = ask in #value-fabric-architecture Slack channel.