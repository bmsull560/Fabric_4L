# Environment Auth Fallback Policy

Fabric_4L authentication and tenant fallback behavior is environment-bound.

| Environment | Auth fallback policy | Tenant fallback policy | Secret policy |
| --- | --- | --- | --- |
| Production | Fail closed. Dev auth bypass and mock auth are forbidden. | Fail closed. Missing tenant context must reject the request. | Required injected secrets only. No optional defaults. |
| Staging | Fail closed. Mirrors production security behavior. | Fail closed. Missing tenant context must reject the request. | Required injected secrets only. No optional defaults. |
| CI | Deterministic test identities only. No runtime dev bypass in prod-like settings. | Deterministic fixture tenants only. No silent `system` fallback. | Test secrets must be explicit and non-production. |
| Local development | Warning-only fallbacks are allowed only when explicitly enabled. | Local fixture tenants may be used for isolated development flows. | Local defaults may be used only outside production-like environments. |

Production-like environments are identified by `ENVIRONMENT`, `APP_ENV`, or `VF_ENV`
values of `production`, `prod`, `staging`, `stage`, or `preview`. In those
environments, startup validation must reject fallback secrets, development auth
bypass flags, and implicit tenant defaults.
