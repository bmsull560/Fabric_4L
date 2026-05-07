# Critical CI Gates: Service Mapping, Ownership, and Escalation

This document defines the merge-blocking critical-gate stage configured in `.github/workflows/critical-gates.yml`.

## Merge policy

- The `Critical Gates` workflow runs on every PR to `main` and on pushes to `main`.
- `critical-gates-merge-blocker` hard-fails if any individual gate fails.
- Each gate publishes machine-readable JSON evidence and raw execution logs as build artifacts.

## Gate map

| Gate ID | Gate intent | Critical service | Primary owner | Escalation |
|---|---|---|---|---|
| `auth-coverage` | Auth coverage checks for endpoint protection regressions | `layer3` | `@value-fabric/security-leads` | `@value-fabric/ciso` |
| `tenant-isolation-hostile` | Hostile tenant isolation regression checks | `layer4` | `@value-fabric/security-leads` | `@value-fabric/backend-leads` |
| `openapi-drift` | OpenAPI drift detection from generated specs | `layer2` | `@value-fabric/architects` | `@value-fabric/maintainers` |
| `production-config-policy` | Production config policy validation | `layer5` | `@value-fabric/sre-leads` | `@value-fabric/security-leads` |
| `production-config-policy-layer6` | Production blocker/policy tests coverage | `layer6` | `@value-fabric/sre-leads` | `@value-fabric/qa-leads` |

## Evidence artifact contract

Each gate emits:

- `artifacts/critical-gates/<gate-id>.json`
- `artifacts/critical-gates/<gate-id>.log`

JSON fields:

- `gate`
- `service`
- `owner`
- `escalation`
- `command`
- `status` (`pass` or `fail`)
- `exit_code`
- `timestamp_utc`
