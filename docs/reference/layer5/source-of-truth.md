# Layer 5 source of truth and compatibility shims

## Canonical runtime package

Layer 5 implementation source of truth is:

- `services/layer5-ground-truth/src/layer5_ground_truth`

All service startup, migrations, tests, and imports should reference `layer5_ground_truth.*`.

## Import entry points

- Service startup: `layer5_ground_truth.api.main:app`
- API routers and schemas: `layer5_ground_truth.api.*`
- Ground-truth models and services: `layer5_ground_truth.models.*` and `layer5_ground_truth.services.*`
- Migrations: `layer5_ground_truth.migrations.env` and `layer5_ground_truth.migrations.versions.*`
- Tests: import canonical modules from `layer5_ground_truth.*`

## Compatibility path

`value_fabric/layer5` is now a compatibility shim tree only. Modules in this tree must only import/re-export from canonical `layer5_ground_truth` modules.

## Deprecation timeline

- **Now (May 12, 2026):** shim compatibility path retained to avoid breaking existing imports.
- **Next hardening phase:** migrate all remaining external imports from `value_fabric.layer5.*` to `layer5_ground_truth.*`.
- **Removal target review:** 2026-09-30, after import-usage reaches zero and release notes communicate the breaking change.
