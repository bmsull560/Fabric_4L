# Repository Config Policy Checker

This repository enforces a CI guardrail for **dev-only insecure auth toggles**.

## Enforced flags

- `ALLOW_INSECURE_DEV_AUTH_BYPASS`
- `JWT_FALLBACK_TO_QUERY_PARAM`

`true` values are blocked in production-like manifests and startup settings.

## Scan scope

The checker (`scripts/ci/check_config_policy.py`) scans:

- `docker-compose*.yml`
- `k8s/**`
- service settings modules (`services/**/src/**/*config.py`, `services/**/src/**/*settings.py`)
- backend env settings modules (`packages/config/src/env/*.ts`)

## Accepted dev-only locations

The only accepted manifest locations for dev-only `true` values are:

- `docker-compose.dev.yml`
- `docker-compose.e2e.yml`
- `docker-compose.release-smoke.yml`

All other scanned files fail CI if these flags are set to truthy values.

## Explicit environment scoping requirement

For settings modules, any dev-only allowance must include explicit development scoping markers (for example `ENVIRONMENT=development` / equivalent checks).

Policy source of truth:

- `contracts/config-policy/config_policy.yml`

## CI integration

The guard runs in PR checks before merge:

- Workflow job: `structural-preflight`
- Step: `Run repository config policy guardrail`
