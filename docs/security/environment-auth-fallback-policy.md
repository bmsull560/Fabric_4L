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

## Startup failure modes (production-like)

Startup validation is expected to **fail closed** when any of the following are true:

- `JWT_SECRET` is missing.
- `JWT_SECRET` matches known default/test placeholders (for example `changeme`, `test-secret`, `your-secret`).
- `JWT_SECRET` is shorter than 32 characters.
- `DATABASE_URL` points to a non-PostgreSQL backend for tenant-scoped services.
- `DATABASE_URL` uses a known PostgreSQL superuser role (`postgres`, `rdsadmin`, `cloudsqladmin`, `azure_superuser`), because superusers bypass RLS.

## Startup summary contract expectations

`get_startup_summary()` now includes RLS and degraded-control shape keys that operators and tests can rely on:

- `rls_status`: one of `active`, `disabled`, `superuser_bypass`.
- `rls_enforcement`: object with:
  - `supported_backend` (bool)
  - `superuser_connection` (bool)
  - `enforced` (bool)
  - `status` (`enforced`, `unsupported_backend`, `superuser_bypass`, `missing_database_url`, `invalid_database_url`)
- `degraded_control_status`: object with:
  - `is_degraded` (bool)
  - `controls` (list of degraded control names)
