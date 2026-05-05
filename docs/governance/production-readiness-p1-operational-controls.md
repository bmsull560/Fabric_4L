# P1 Production-Readiness Operational Controls

The readiness assessment identifies feature flags, notifications, tenant-scoped quotas, and SDK/CLI maturity as P1 production-readiness concerns. Repository inspection shows that Fabric_4L already contains implementation assets for these areas. The remaining work is to make the operational contract explicit and require live evidence before claiming production readiness.

## P1 Gate Matrix

| Gate | Repository foundation | Current status | Production evidence still required |
|---|---|---|---|
| Notifications and alert routing | Alertmanager assets, notification service, notification skill contract, tests, and `config/production-readiness/notification_alert_policy.json`. | Foundation ready; receiver evidence required. | Real receiver delivery, external secret resolution, SEV-1 paging, workflow pause notification, and retry/dead-letter visibility. |
| Feature flags | Kubernetes feature-flag assets, shared feature-flag modules, Layer 4 feature-flag API/service/models, migrations, and `config/production-readiness/feature_flag_rollout_policy.json`. | Foundation ready; runtime rollout evidence required. | Unknown-flag denial, tenant allow-list enforcement, kill-switch proof, high-risk audit events, and expired-flag detection. |
| Tenant quotas and rate limiting | Shared tenant rate limiter, middleware, admin API, Layer 3 rate limiter, tests, and `config/production-readiness/tenant_quota_policy.json`. | Foundation ready; load evidence required. | Two-tenant isolation test, deterministic 429 response, rate-limit headers, noisy-tenant load test, and expiring override audit. |
| SDK and CLI | OpenAPI contracts, generation scripts, Python SDK package, CLI module, SDK docs, and publication workflows. | Foundation ready; package/live smoke evidence required. | Clean build, clean install, staging API smoke, drift-free generated clients, and no token leakage in logs or evidence. |

## Operational Assertion Rule

P1 controls should be reported as **foundation ready** when repository files, contracts, and tests exist. They should be reported as **production PASS** only after their live operational behavior is demonstrated with tenant context, receiver delivery, externalized secrets, and redacted evidence artifacts.
