# Layer 5 source of truth and compatibility shims

## Canonical runtime package

Layer 5 implementation source of truth is:

- `services/layer5-ground-truth/src/layer5_ground_truth`

All service startup, migrations, tests, and imports should reference `layer5_ground_truth.*`.

## Compatibility path

`value_fabric/layer5` is now a compatibility shim tree only. Modules in this tree must only import/re-export from canonical `layer5_ground_truth` modules.

## Deprecation timeline

- **Now (May 12, 2026):** shim compatibility path retained to avoid breaking existing imports.
- **Next hardening phase:** migrate all remaining external imports from `value_fabric.layer5.*` to `layer5_ground_truth.*`.
- **Removal target:** remove `value_fabric/layer5` shim tree after import-usage reaches zero and release notes communicate the breaking change.
