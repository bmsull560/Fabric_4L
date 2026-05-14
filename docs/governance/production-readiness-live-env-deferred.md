# Production Readiness — Track B Deferred Items

**Created:** 2026-05-14  
**Status:** Open  
**Owner:** Platform SRE + Layer Maintainers  
**Related:** `docs/governance/production-readiness-status-2026-05-14.md`

These items require a live environment (Bunnyshell, Kubernetes cluster, live
databases, live LLM credentials, live identity provider) and cannot be
validated from repository files alone. They must be completed before
customer-facing traffic is routed to this deployment.

---

## Deployment and Service Health

| Item | Dependency | Owner | Target | Evidence Required |
|---|---|---|---|---|
| All 6 services deploy successfully | K8s cluster | SRE | Next sprint | `kubectl get pods -n fabric-4l-prod` — all Running |
| Health checks pass for all layers | Live environment | SRE | Next sprint | `curl /health` returns 200 for each service |
| Readiness checks pass for all layers | Live environment | SRE | Next sprint | `curl /ready` returns 200 for each service |
| Metrics endpoints reachable by Prometheus | Live monitoring | SRE | Next sprint | Prometheus targets page shows all 6 layers UP |
| Logs visible in log aggregation | Live logging | SRE | Next sprint | Structured logs with correlation IDs visible |
| Alerts wired and firing correctly | Live alerting | SRE | Next sprint | Test alert fires and routes to correct channel |

---

## Database and Migration

| Item | Dependency | Owner | Target | Evidence Required |
|---|---|---|---|---|
| Migrations apply from empty database | Live PostgreSQL | Backend Leads | Next sprint | `alembic upgrade head` exits 0 for all services |
| Migrations apply from current staging database | Staging PostgreSQL | Backend Leads | Next sprint | `alembic upgrade head` exits 0 against staging |
| Migrations downgrade where supported | Live PostgreSQL | Backend Leads | Next sprint | `alembic downgrade -1` exits 0 for all services |
| RLS policies active and tested | Live PostgreSQL | Backend Leads | Next sprint | Cross-tenant query returns 0 rows |
| Seed scripts work in non-production only | Staging environment | Backend Leads | Next sprint | Seed endpoint returns 200 in staging, 403 in production |

---

## Background Jobs and Async Processing

| Item | Dependency | Owner | Target | Evidence Required |
|---|---|---|---|---|
| Celery workers start and process tasks | Live Redis + workers | Layer 1 Maintainers | Next sprint | Worker logs show task received and completed |
| Redis/queue connectivity works | Live Redis | Layer 1 Maintainers | Next sprint | `redis-cli ping` returns PONG from worker pod |
| Task retry policy fires on failure | Live environment | Layer 1 Maintainers | Next sprint | Injected failure triggers retry with backoff |
| Dead-letter queue behavior observable | Live environment | Layer 1 Maintainers | Next sprint | Failed task appears in DLQ after max retries |
| LangGraph checkpoint persistence works | Live PostgreSQL | Layer 4 Maintainers | Next sprint | Workflow resumes from checkpoint after restart |
| Background tasks include tenant context | Live environment | Layer 4 Maintainers | Next sprint | Worker logs show `tenant_id` in task context |

---

## Knowledge Graph

| Item | Dependency | Owner | Target | Evidence Required |
|---|---|---|---|---|
| Neo4j connectivity works | Live Neo4j | Layer 3 Maintainers | Next sprint | `RETURN 1` query succeeds |
| Graph schema initialization works | Live Neo4j | Layer 3 Maintainers | Next sprint | Constraints and indexes created on startup |
| Tenant-scoped graph constraints applied | Live Neo4j | Layer 3 Maintainers | Next sprint | Cross-tenant node query returns 0 results |
| Community Edition constraint handling | Live Neo4j CE | Layer 3 Maintainers | Next sprint | Service starts without Enterprise-only features |
| Graph query endpoint works | Live Neo4j | Layer 3 Maintainers | Next sprint | `/entity/traverse` returns valid subgraph |
| Hybrid search works | Live Neo4j + pgvector | Layer 3 Maintainers | Next sprint | `/search` returns ranked results |

---

## End-to-End Workflows

| Item | Dependency | Owner | Target | Evidence Required |
|---|---|---|---|---|
| Full P0 Playwright workflows pass | Live frontend + backend | Frontend + QA | Next sprint | Playwright report: 0 failures on P0 suite |
| Auth lifecycle E2E works | Live identity provider | Frontend + Security | Next sprint | Login → token → API call → logout cycle passes |
| Account creation flow works | Live stack | Product + Backend | Next sprint | New account created, tenant isolated |
| Source ingestion flow works | Live stack | Layer 1 Maintainers | Next sprint | Source ingested, job completes, status = done |
| Extraction flow works | Live stack | Layer 2 Maintainers | Next sprint | Entities extracted, provenance recorded |
| ROI/value calculator works | Live stack | Layer 4 Maintainers | Next sprint | Formula resolves, scenario output generated |
| Business case export works | Live stack | Layer 4 Maintainers | Next sprint | PDF/export generated with grounded evidence |
| Traceability: source → evidence → driver → output | Live stack | All teams | Next sprint | Each output links back to source document |

---

## Live Observability Validation

| Item | Dependency | Owner | Target | Evidence Required |
|---|---|---|---|---|
| Grafana dashboards show live data | Live monitoring | SRE | Next sprint | Dashboard screenshots with non-zero metrics |
| Alertmanager routes alerts correctly | Live alerting | SRE | Next sprint | Test alert delivered to correct channel |
| SLO dashboards show burn rate | Live monitoring | SRE | Next sprint | SLO dashboard shows current error budget |
| Distributed tracing active | Live tracing | SRE | Next sprint | Trace visible in Jaeger/Tempo for P0 request |

---

## External Provider Validation

| Item | Dependency | Owner | Target | Evidence Required |
|---|---|---|---|---|
| LLM provider credentials work | Live LLM API | Layer 4 Maintainers | Next sprint | Extraction and agent workflow complete with real LLM |
| Enterprise SSO/OIDC works | Live identity provider | Security | Next sprint | SSO login flow completes, JWT issued |
| Billing/metering webhook works | Live billing provider | Platform | Next sprint | Usage event recorded in billing system |

---

## Completion Criteria

Track B is complete when all items above have:
1. Evidence captured (screenshot, log excerpt, test report, or command output).
2. Evidence committed to `signoff-evidence/` or linked from this document.
3. This document updated with `Status: Complete` and the evidence date.

Until Track B is complete, the production deployment must not receive
customer-facing traffic without explicit product and security sign-off.
