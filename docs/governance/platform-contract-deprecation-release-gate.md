# Platform Contract Deprecation Release Gate

This policy defines the **release gate** that enforces high-risk deprecations listed in:

- `docs/platform-contract/DEPRECATION_MAP.md`

## CI Assertion Location

- Test suite: `tests/release/test_platform_contract_deprecations.py`
- Scope: canonical runtime paths only
  - `value_fabric/`
  - `services/`
  - `apps/web/`
- Exclusions: documentation/examples and non-runtime build artifacts (for example `docs/`, `examples/`, `node_modules/`, `dist/`, `build/`).

## Pass/Fail Rules

1. High-risk deprecations are encoded as explicit rule IDs (`PCD-001`, `PCD-002`, ...).
2. Each rule has:
   - deprecated pattern string
   - canonical replacement API/pattern
   - canonical module path guidance
   - deadline date
3. If current date is **before** deadline, the assertion is skipped.
4. If current date is **on/after** deadline, any remaining matches in canonical runtime paths fail the build.

## Exception Handling

Exceptions must be documented in:

- `docs/governance/deprecations.json` → `exceptions[]`

Each exception must include:

- unique `id`
- `status` of `approved` or `active`
- `appliesTo` containing the specific deprecation rule ID (`PCD-###`)

If no qualifying exception ID exists, the test fails with a message describing how to register a waiver.

## Failure Message Requirements

Failing assertions include:

- rule ID
- deprecated pattern
- deadline
- replacement API/pattern
- canonical module path to migrate toward
- list of offending files
- exception status summary

This allows release managers to audit gate outcomes quickly without tracing implementation internals.
