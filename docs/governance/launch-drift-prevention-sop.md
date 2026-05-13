# Launch Drift Prevention SOP

## Purpose

This SOP defines the minimum approval path for launch-affecting changes that can introduce contract
drift, tenant-isolation drift, or compatibility-shim drift. Use it before merging release-bound
changes and during release-branch hardening.

## Scope

Apply this SOP when a change affects any of the following:

- OpenAPI, JSON Schema, or API response/request shape
- Backend route behavior or frontend consumers of governed API contracts
- Tenant-scoped reads, writes, auth context propagation, or RLS/query isolation behavior
- Compatibility shims, deprecated aliases, mirrored source trees, or adapter-only surfaces tracked
  in `docs/governance/compatibility-debt-registry.md`

## Required Approvals

| Change type | Required reviewer/owner | Required evidence before merge | Release-branch expectation |
|---|---|---|---|
| Contract shape change | Platform contract owner or service owner for the affected layer | Updated contract source (`contracts/openapi/` or `contracts/jsonschema/`), consumer impact note, tests updated, rollback note for breaking changes | Release captain confirms contract checklist items remain checked and PR body declares contract impact |
| Tenant isolation change | Service owner plus security/tenant-isolation reviewer | Auth-context path reviewed, tenant-scoped queries/writes validated, hostile or regression test added/updated, no request-body tenant trust regression | Release captain confirms tenant-isolation note is explicit in PR and launch checklist remains checked |
| Compatibility shim change | Compatibility-debt owner for the shim plus owning service team | Registry entry added/updated, removal target reviewed, downstream consumer impact noted, shim labels/acknowledgment present | Release captain confirms shim impact is declared and shim governance checklist remains checked |

## PR Requirements

Every in-scope PR must include:

- `Contract shape impact`
- `Tenant isolation impact`
- `Compatibility shim impact`

Use explicit values such as `None`, `Additive`, `Breaking`, `Reviewed-no-impact`, `Added`, or
`Removed`, plus a short rationale when the impact is not `None`.

## Release-Branch Rules

On `release/*` branches:

- Do not leave the launch governance checklist items unchecked in
  `docs/launch-checklists/platform-launch.md`.
- Do not merge an in-scope PR without the required PR governance fields.
- Do not merge a shim change without updating the compatibility debt registry or explicitly stating
  why the registry is unchanged.

## Evidence Links

- Canonical contract: [`docs/contract.md`](../contract.md)
- Governance entry point: [`docs/governance.md`](../governance.md)
- Compatibility registry: [`docs/governance/compatibility-debt-registry.md`](compatibility-debt-registry.md)
- PR template: [`.github/pull_request_template.md`](../../.github/pull_request_template.md)
