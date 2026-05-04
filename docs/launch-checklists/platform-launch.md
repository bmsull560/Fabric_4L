# Value Fabric Platform — Controlled Launch Checklist

**Date:** 2026-05-04  
**Status:** PRE-LAUNCH PREPARATION  
**Sprint:** Sprint 4 - Release Hardening, Documentation, and Launch Rehearsal

This checklist covers readiness for a controlled production launch of the Value Fabric platform. It covers all layers (L1-L6), frontend, and infrastructure components.

---

## 1. Environment & Secrets

### 1.1 Production Environment Configuration

- [ ] `CREDENTIALS_MASTER_KEY` configured in production (43-char Fernet key)
- [ ] `OPENAI_API_KEY` configured with production quota
- [ ] `ANTHROPIC_API_KEY` configured with production quota
- [ ] `JWT_SECRET` configured with strong secret (>32 characters)
- [ ] `NEO4J_PASSWORD` configured with strong password
- [ ] `DATABASE_URL` configured with production PostgreSQL instance
- [ ] `REDIS_URL` configured with production Redis instance
- [ ] `NEO4J_URL` configured with production Neo4j instance
- [ ] `.env.example` updated with all production variables

### 1.2 Environment-Specific Settings

- [ ] `ENVIRONMENT=production` set for all services
- [ ] `ALLOW_INSECURE_DEV_AUTH_BYPASS=false` enforced
- [ ] `JWT_FALLBACK_TO_QUERY_PARAM=false` enforced
- [ ] `CORS_ORIGINS` lists only trusted production origins
- [ ] No wildcard CORS origins in production

---

## 2. Database

### 2.1 PostgreSQL Configuration

- [ ] PostgreSQL instance provisioned with production specs
- [ ] Connection pool configured for production load
- [ ] SSL/TLS enforced for database connections
- [ ] Row-Level Security (RLS) policies applied
- [ ] Database migrations applied (Alembic upgrade head)
- [ ] Migration rollback tested (Alembic downgrade -1)
- [ ] Backup schedule configured
- [ ] Point-in-time recovery enabled

### 2.2 Redis Configuration

- [ ] Redis instance provisioned with production specs
- [ ] Redis persistence (RDB/AOF) configured
- [ ] Redis TLS enabled
- [ ] Redis authentication configured
- [ ] Redis cluster or sentinel configured for high availability

### 2.3 Neo4j Configuration

- [ ] Neo4j instance provisioned with production specs
- [ ] Neo4j authentication configured
- [ ] Neo4j TLS enabled
- [ ] Vector indexes created and verified
- [ ] Graph indexes created and verified
- [ ] Neo4j backup schedule configured

---

## 3. Backend Hardening

### 3.1 Layer 1: Ingestion Service

- [ ] Rate limiting enforced
- [ ] PII scanner operational
- [ ] robots.txt checker operational
- [ ] Playwright crawler configured with production timeouts
- [ ] Proxy rotation configured (if required)
- [ ] Job queue (Celery/Redis) operational
- [ ] Monitoring and metrics configured

### 3.2 Layer 2: Extraction Service

- [ ] LLM client configured with production API keys
- [ ] Cost tracking enabled
- [ ] Exponential backoff retry logic enabled
- [ ] Redis job store operational (no in-memory fallback in production)
- [ ] PostgreSQL pending ingestion store operational (no SQLite fallback in production)
- [ ] I-02 production fail-closed tests passing

### 3.3 Layer 3: Knowledge Graph Service

- [ ] Neo4j driver configured with production credentials
- [ ] Vector indexes operational
- [ ] GraphRAG query endpoint tested
- [ ] Hybrid search operational
- [ ] Cross-layer connectivity verified
- [ ] API rate limiting enforced
- [ ] Health check endpoint operational

### 3.4 Layer 4: Agents Service

- [ ] LangGraph state machine operational
- [ ] Checkpointing configured (AsyncPostgresSaver)
- [ ] Resume endpoint operational
- [ ] Tool registry populated
- [ ] Workflow scheduler operational
- [ ] Human-in-the-loop integration tested
- [ ] Agent provenance tracking enabled

### 3.5 Layer 5: Ground Truth Service

- [ ] TruthObject model operational
- [ ] Validation state machine operational
- [ ] Maturity ladder (0-5) operational
- [ ] Freshness monitor operational
- [ ] Auto-advancement logic tested
- [ ] Dispute resolution workflow tested
- [ ] I-02 production fail-closed tests passing

### 3.6 Layer 6: Benchmarks Service

- [ ] Benchmark harness operational
- [ ] Evaluation storage configured
- [ ] Metrics export configured
- [ ] CI coverage gate operational

### 3.7 Shared Libraries

- [ ] Tenant context middleware operational
- [ ] Authentication/authorization library operational
- [ ] Audit logging operational
- [ ] Identity service operational
- [ ] Import boundary enforcement operational

---

## 4. Frontend

### 4.1 Build & Deployment

- [ ] Production build successful (`npm run build`)
- [ ] Environment variables configured for production
- [ ] Static asset optimization enabled
- [ ] Source maps disabled for production
- [ ] CSP headers configured

### 4.2 API Integration

- [ ] TanStack Query client configured
- [ ] API endpoints wired to real backend
- [ ] Error handling implemented
- [ ] Loading states implemented
- [ ] Authentication UI connected (if SSO/OIDC configured)

### 4.3 Contract Tests

- [ ] Frontend contract tests passing
- [ ] No placeholder contract tests
- [ ] Type synchronization verified

### 4.4 E2E Tests

- [ ] Critical E2E tests passing
- [ ] No skipped critical E2E tests
- [ ] Golden path tests passing
- [ ] Layer UI validation tests passing
- [ ] Tenant isolation tests passing
- [ ] Agent grounding tests passing
- [ ] Calculation/evidence tests passing
- [ ] Approval/review tests passing
- [ ] Export workflow tests passing

---

## 5. Infrastructure

### 5.1 Kubernetes Configuration

- [ ] Kubernetes cluster provisioned
- [ ] Namespaces configured (dev, staging, production)
- [ ] Resource limits configured
- [ ] HPA (Horizontal Pod Autoscaler) configured
- [ ] PDB (Pod Disruption Budget) configured
- [ ] Network policies configured
- [ ] Service accounts configured
- [ ] RBAC configured

### 5.2 Service Deployments

- [ ] Layer 1 deployment operational
- [ ] Layer 2 deployment operational
- [ ] Layer 3 deployment operational
- [ ] Layer 4 deployment operational
- [ ] Layer 5 deployment operational
- [ ] Layer 6 deployment operational
- [ ] Frontend deployment operational
- [ ] All services healthy

### 5.3 Ingress & Routing

- [ ] Ingress controller configured
- [ ] TLS certificates configured
- [ ] Routing rules configured
- [ ] Gateway API or Istio configured (if applicable)

### 5.4 Monitoring

- [ ] Prometheus configured
- [ ] Grafana dashboards configured
- [ ] Alertmanager configured
- [ ] Alerting rules configured
- [ ] SLOs defined
- [ ] Error budget tracking enabled

### 5.5 Logging

- [ ] Structured logging enabled
- [ ] Log aggregation configured
- [ ] Correlation IDs propagated
- [ ] Sensitive data redaction verified

### 5.6 Secrets Management

- [ ] Vault or secret manager configured
- [ ] Secret rotation policy defined
- [ ] Secret audit logging enabled
- [ ] No secrets in code or configuration

---

## 6. Security

### 6.1 Authentication & Authorization

- [ ] JWT authentication operational
- [ ] OIDC/SAML SSO configured (if applicable)
- [ ] RBAC policies defined
- [ ] Tenant isolation verified
- [ ] Cross-tenant API tests passing
- [ ] Auth boundary tests passing

### 6.2 Network Security

- [ ] VPC/private network configured
- [ ] Firewall rules configured
- [ ] TLS enforced everywhere
- [ ] API gateway configured (if applicable)

### 6.3 Container Security

- [ ] Container images scanned for vulnerabilities
- [ ] Non-root user enforced
- [ ] Read-only filesystem enforced
- [ ] Resource limits enforced
- [ ] Security context configured

### 6.4 Dependency Security

- [ ] Python dependencies audited (pip-audit)
- [ ] Node.js dependencies audited (pnpm audit)
- [ ] SBOMs generated
- [ ] Vulnerability policy enforced

### 6.5 Supply Chain

- [ ] Gitleaks scan passing
- [ ] Dependency review passing
- [ ] Signed commits enforced (if applicable)

---

## 7. Observability

### 7.1 Metrics

- [ ] Prometheus metrics exported
- [ ] Custom business metrics defined
- [ ] LLM cost metrics tracked
- [ ] Request/response time metrics tracked
- [ ] Error rate metrics tracked

### 7.2 Tracing

- [ ] Distributed tracing configured
- [ ] Request ID propagation verified
- [ ] Trace sampling configured

### 7.3 Alerting

- [ ] Critical alerts defined
- [ ] Alert routing configured
- [ ] On-call rotation defined
- [ ] Escalation policy defined
- [ ] Runbooks linked to alerts

---

## 8. Testing

### 8.1 Unit Tests

- [ ] Backend unit tests passing
- [ ] Frontend unit tests passing
- [ ] Coverage threshold met (80%+)

### 8.2 Integration Tests

- [ ] Cross-layer integration tests passing
- [ ] Database integration tests passing
- [ ] API integration tests passing

### 8.3 Contract Tests

- [ ] OpenAPI contract tests passing
- [ ] Frontend contract tests passing
- [ ] Type synchronization verified

### 8.4 Security Tests

- [ ] Security regression gate passing
- [ ] I-02 production fail-closed tests passing
- [ ] Tenant isolation tests passing
- [ ] Auth boundary tests passing

### 8.5 Performance Tests

- [ ] Load tests passing
- [ ] Performance benchmarks passing
- [ ] SLOs met

---

## 9. Documentation

### 9.1 Architecture Documentation

- [ ] Architecture diagrams current
- [ ] ADRs (Architecture Decision Records) up to date
- [ ] API documentation current
- [ ] Runbooks current

### 9.2 Operational Documentation

- [ ] Deployment runbooks current
- [ ] Troubleshooting runbooks current
- [ ] Onboarding documentation current
- [ ] Command reference current

### 9.3 Release Documentation

- [ ] Release notes prepared
- [ ] Migration guides prepared
- [ ] Rollback documentation prepared
- [ ] Launch checklist (this document) complete

---

## 10. Rollback Plan

### 10.1 Database Rollback

- [ ] Database backup verified
- [ ] Migration rollback tested (Alembic downgrade -1)
- [ ] Point-in-time recovery tested

### 10.2 Application Rollback

- [ ] Previous Docker image tagged and available
- [ ] Kubernetes rollback procedure documented
- [ ] Argo Rollouts (if applicable) configured

### 10.3 Configuration Rollback

- [ ] Previous configuration versioned
- [ ] Configuration rollback procedure documented

### 10.4 Data Rollback

- [ ] Data migration rollback procedure documented
- [ ] Data backup/restore procedure tested

---

## 11. Launch Decision

### 11.1 Pre-Launch Checklist

- [ ] All P0 items complete
- [ ] All P1 items complete or accepted risk documented
- [ ] All P2 items documented as post-launch backlog
- [ ] Stakeholder sign-off obtained
- [ ] On-call team notified
- [ ] Communication plan prepared

### 11.2 Launch Readiness Assessment

- [ ] Launch readiness percentage calculated
- [ ] Blockers identified and resolved
- [ ] Accepted risks documented with owner and date
- [ ] Go/No-Go decision made

### 11.3 Launch Execution

- [ ] Launch window scheduled
- [ ] Launch team assembled
- [ ] Launch procedure executed
- [ ] Launch verification performed
- [ ] Launch announcement sent

---

## 12. Post-Launch

### 12.1 Monitoring

- [ ] Monitoring dashboards reviewed
- [ ] Alert thresholds validated
- [ ] Error rates within acceptable range
- [ ] Performance metrics within SLO

### 12.2 Validation

- [ ] Smoke tests passing
- [ ] Critical user journeys tested
- [ ] Data integrity verified
- [ ] Tenant isolation verified

### 12.3 Communication

- [ ] Stakeholders notified of launch success
- [ ] Users notified of new features
- [ ] Support team trained
- [ ] Documentation published

---

## Known Limitations & GA Blockers

### Current Limitations (Acceptable for Controlled Launch)

- [ ] **OAuth Authorization Flow for CRM integrations not implemented**
  - Current: Manual token entry required
  - Impact: Admin burden for initial setup
  - Mitigation: Documented in runbook
  - GA Requirement: Must implement before general availability

- [ ] **Background sync uses asyncio.create_task, not Celery**
  - Current: Sync jobs ephemeral, lost on pod restart
  - Impact: No durable job queue for single-replica pilots
  - Mitigation: Scheduled sync robust for single-replica
  - GA Requirement: Must migrate to Celery/Redis before multi-replica

### GA Blockers (Must Resolve Before General Availability)

- [ ] Implement OAuth authorization flow for all integrations
- [ ] Migrate background sync to Celery/Redis queue
- [ ] Add comprehensive E2E tests for all critical flows
- [ ] Add dedicated sync_jobs history table
- [ ] Configure Prometheus export for all metrics
- [ ] Implement full SLO monitoring and alerting
- [ ] Complete disaster recovery testing
- [ ] Complete security penetration testing

---

## Appendix: Evidence Paths

| Evidence Category | Evidence Path |
|------------------|---------------|
| Security Regression Gate | `fabric_audit/i04_mandatory_security_regression_gate_evidence.md` |
| E2E Validation | `docs/validation/e2e_traceability_matrix.md` |
| Deep Validation Failures | `docs/validation/deep_validation_initial_failures.md` |
| Contract Audit | `reports/CONTRACT_AUDIT_REPORT.md` |
| Dead Code Sweep | `reports/DEAD_CODE_SWEEP_REPORT.md` |
| Production Readiness | `docs/operations/tenant-management-phase-3-control-plane.md` |

---

**Launch Decision:** PENDING  
**Next Review:** After CI job execution and launch rehearsal  
**Owner:** Release Manager  
**Date:** 2026-05-04
