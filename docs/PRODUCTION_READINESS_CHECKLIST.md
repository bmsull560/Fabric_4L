# Production Readiness Checklist

> **Purpose:** Pass/fail criteria for production deployments.  
> **Owner:** Platform Engineering  
> **Last Updated:** 2026-04-14  
> **Related:** [Supply Chain Security](docs/supply-chain/SUPPLY_CHAIN_SECURITY.md)

---

## How to Use

Before any production deployment:

1. Run `make verify` — all checks must pass
2. Run `scripts/security/verify-artifact.sh <image>` for every image being deployed
3. Walk through each section below and mark PASS or FAIL
4. **Any FAIL in a P0 category blocks deployment**

---

## Security

| # | Check | Criteria | Priority | Status |
|---|-------|----------|----------|--------|
| S1 | **Artifact signatures verified** | `cosign verify` passes for all images with correct OIDC identity | P0 | ✅ PASS |
| S2 | **SLSA provenance verified** | `cosign verify-attestation --type slsaprovenance` passes for all images | P0 | ✅ PASS |
| S3 | **No HIGH/CRITICAL CVEs** | Trivy container scan shows 0 unfixed HIGH/CRITICAL vulnerabilities | P0 | ✅ PASS |
| S4 | **No secrets in source** | gitleaks scan passes with 0 findings on full git history | P0 | ✅ PASS |
| S5 | **SAST clean** | CodeQL + bandit report 0 MEDIUM+ findings | P0 | ✅ PASS |
| S6 | **Dependency audit clean** | pip-audit (HIGH+) and pnpm audit (CRITICAL) pass | P0 | ✅ PASS |
| S7 | **Non-root containers** | All 7 images run as non-root user (verified by CI) | P0 | ✅ PASS |
| S8 | **Network policies active** | Deny-all default + per-layer allowlists applied | P0 | ✅ PASS |
| S9 | **DAST baseline** | OWASP ZAP baseline scan completes against all API surfaces | P1 | ✅ PASS |
| S10 | **SBOMs generated** | CycloneDX SBOM exists for every deployed image | P1 | ✅ PASS |
| S11 | **Secrets via Vault/Infisical** | No secrets in K8s manifests; all injected via ExternalSecret | P0 | ✅ PASS |
| S12 | **JWT signing key rotated** | JWT signing key age < 30 days | P1 | ✅ PASS |
| S13 | **API key rotation** | All API keys age < 90 days | P1 | ✅ PASS |
| S14 | **RBAC middleware active** | `shared/identity/` middleware applied to all API routes | P0 | ✅ PASS |
| S15 | **Audit logging active** | Append-only audit log operational with trigger protection | P0 | ✅ PASS |
| S16 | **Zero-trust validation** | `scripts/security/zero_trust_checks.sh` passes all 9 checks | P0 | ✅ PASS |
| S17 | **Dependency review on PR** | `actions/dependency-review-action` blocks HIGH+ new deps | P1 | ✅ PASS |
| S18 | **Threat model current** | `docs/security/threat-model.md` updated within last 90 days | P2 | ✅ PASS |

---

## Reliability

| # | Check | Criteria | Priority | Status |
|---|-------|----------|----------|--------|
| R1 | **Health checks configured** | Every Dockerfile has HEALTHCHECK; K8s has liveness + readiness probes | P0 | ✅ PASS |
| R2 | **Pod Disruption Budgets** | PDB configured for L2, L3, L4, frontend (`minAvailable ≥ 1`) | P0 | ✅ PASS |
| R3 | **Rolling update strategy** | `maxUnavailable: 0` ensures zero-downtime deploys | P0 | ✅ PASS |
| R4 | **Rollback runbook** | `docs/runbooks/deployment-rollback.md` exists and tested | P0 | ✅ PASS |
| R5 | **DR policy documented** | `docs/reliability/dr-policy.md` exists with RTO/RPO targets | P0 | ✅ PASS |
| R6 | **DR gameday executed** | Region loss + service failover drills documented | P1 | ✅ PASS |
| R7 | **Backup/restore tested** | `make test-backup-drills` passes | P1 | ✅ PASS |
| R8 | **SLO defined** | `docs/slo/performance-slo.v1.json` with latency + error rate targets | P0 | ✅ PASS |
| R9 | **Alerting configured** | Prometheus rules + AlertManager → Slack for all critical alerts | P0 | ✅ PASS |
| R10 | **Incident runbooks** | Runbooks exist for all critical alert types (10+ runbooks) | P0 | ✅ PASS |
| R11 | **Postmortem template** | `docs/operations/postmortem-template.md` exists | P1 | ✅ PASS |
| R12 | **Smoke tests post-deploy** | `smoke-gate.yml` validates core functionality after deployment | P0 | ✅ PASS |

---

## Scalability

| # | Check | Criteria | Priority | Status |
|---|-------|----------|----------|--------|
| SC1 | **HPA configured** | Horizontal Pod Autoscaler for L2, L4, frontend | P0 | ✅ PASS |
| SC2 | **Resource limits set** | CPU and memory limits defined for all K8s deployments | P0 | ✅ PASS |
| SC3 | **Load tests passing** | k6 critical-path suite meets SLO thresholds | P1 | ✅ PASS |
| SC4 | **Database connection pooling** | Connection limits configured per service | P1 | ✅ PASS |
| SC5 | **Caching strategy** | Redis caching active for hot paths | P1 | ✅ PASS |
| SC6 | **Build parallelization** | Matrix builds for all 7 services | P2 | ✅ PASS |
| SC7 | **Docker layer caching** | BuildKit GHA cache enabled (`type=gha,mode=max`) | P2 | ✅ PASS |
| SC8 | **Rate limiting** | API rate limits configured (1,000 req/min global) | P0 | ✅ PASS |

---

## Compliance

| # | Check | Criteria | Priority | Status |
|---|-------|----------|----------|--------|
| C1 | **Control matrix current** | `docs/compliance/control-matrix.md` updated, CI-enforced | P0 | ✅ PASS |
| C2 | **Audit log retention** | 7-year retention policy for API access logs | P0 | ✅ PASS |
| C3 | **SBOM retention** | 30-day artifact retention for all SBOMs | P1 | ✅ PASS |
| C4 | **Security evidence bundle** | `release-security-evidence-<sha>` artifact generated per release | P0 | ✅ PASS |
| C5 | **Vulnerability disclosure** | `docs/trust/coordinated-vulnerability-disclosure.md` published | P0 | ✅ PASS |
| C6 | **Vendor risk policy** | `docs/trust/vendor-risk-policy.md` exists with assessment criteria | P1 | ✅ PASS |
| C7 | **Data commitments** | `docs/trust/customer-data-commitments.md` published | P1 | ✅ PASS |
| C8 | **NIST SSDF alignment** | All PO/PS/PW/RV practices mapped to controls | P0 | ✅ PASS |
| C9 | **SLSA Level 3** | Provenance attestations generated and verifiable | P0 | ✅ PASS |
| C10 | **Accessibility** | axe-core critical scan passes for all public pages | P1 | ✅ PASS |

---

## Summary

| Category | Total Checks | P0 Checks | All P0 Pass? |
|----------|-------------|-----------|-------------|
| Security | 18 | 12 | ✅ |
| Reliability | 12 | 8 | ✅ |
| Scalability | 8 | 3 | ✅ |
| Compliance | 10 | 5 | ✅ |
| **Total** | **48** | **28** | **✅** |

---

## Deployment Decision

- **All 28 P0 checks PASS** → ✅ **CLEARED FOR PRODUCTION**
- **Any P0 check FAIL** → ❌ **DEPLOYMENT BLOCKED** — resolve before proceeding
- **P1/P2 failures** → ⚠️ **DEPLOY WITH TRACKING** — create issue and assign owner
