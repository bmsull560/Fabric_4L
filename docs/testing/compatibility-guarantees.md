# Compatibility Guarantees and Removal Targets

This document defines temporary compatibility guarantees for legacy endpoint and model-field aliases, and the target phase/date for removal.

## Policy

- **Temporary compatibility** = behavior preserved only for a bounded migration window.
- **Permanent compatibility** = behavior intentionally kept long-term as part of stable public contract.
- Temporary checks in tests MUST be tagged with `@pytest.mark.temporary_compat` or named with `test_temp_compat__*`.
- Permanent compatibility checks SHOULD be tagged with `@pytest.mark.permanent_compat`.

## Current compatibility guarantees

| Area | Alias / behavior guaranteed | Classification | Target removal phase | Target date |
|---|---|---|---|---|
| Graph API endpoint pathing | Legacy `/api/v1/graph/subgraph` consumer-contract path accepted in compatibility fixtures/contracts | Temporary | **P2** | **2026-07-01** |
| GraphNode field alias | Legacy `type` accepted alongside canonical `entity_type` | Temporary | **P2** | **2026-07-01** |
| Request auth source alias | `source=jwt` and `source=bearer` normalize to `jwt_claim`; `source=api-key` normalizes to `api_key` | Temporary | **P2** | **2026-07-01** |

## Removal process

1. Keep temporary tests visible in CI summary (`compatibility debt` check).
2. At each release, burn down temporary compatibility tests and update this table.
3. Once target date/phase is reached:
   - Remove alias behavior from runtime code.
   - Remove corresponding `temporary_compat` tests.
   - Add/retain `permanent_compat` tests for any remaining guarantees.
