# P0 Production-Readiness Foundations

The readiness assessment identified enterprise SSO/OIDC, central model management, and incident runbooks as P0 gaps. Repository inspection shows that Fabric_4L already contains substantial implementation assets for OIDC, model registry, and operational runbooks. This document turns those assets into explicit production gates so the project can distinguish **repository foundation complete** from **production evidence complete**.

## P0 Gate Matrix

| Gate | Repository foundation | Current status | Production evidence still required |
|---|---|---|---|
| Enterprise SSO/OIDC | Shared OIDC modules, Layer 4 OIDC routes and migrations, OAuth2 proxy deployment assets, and `config/production-readiness/oidc_enterprise_requirements.json`. | Foundation ready; provider evidence required. | Real provider discovery, JWKS validation, authorization-code callback, tenant mapping, logout, and audit events. |
| Model management | Layer 5 model registry models/routes/migrations, Layer 4 and Layer 2 registry clients, registry tests, and `config/production-readiness/model_governance_policy.json`. | Foundation ready; runtime evidence required. | Runtime model selection from registry, promotion/deprecation workflow, rollback drill, and audit-linked approvals. |
| Incident runbooks | Existing runbook directories plus dedicated enterprise OIDC and model registry incident runbooks. | Foundation ready; drill evidence required. | On-call drill or staging incident simulation with owner, response time, closure evidence, and post-incident review. |

## Production Assertion Rule

A P0 gate must not be marked production PASS merely because repository files exist. PASS requires a live or staging environment that exercises the relevant control with external dependencies configured, sensitive values externalized, and evidence captured without secrets.
