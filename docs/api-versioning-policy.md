# API Versioning and Lifecycle Policy

## Purpose

This policy defines API compatibility guarantees, versioning rules, deprecation windows, and the sunset process for Value Fabric APIs.

## Scope

Applies to all externally consumed interfaces, including:

- REST APIs across layers
- Shared contracts in `contracts/openapi/` and `contracts/jsonschema/`
- SDK-facing API surfaces generated from contracts

## Versioning Model

- APIs use **semantic versioning at the API major level** (`v1`, `v2`, ...).
- **Major version** changes indicate breaking changes.
- **Minor/patch** changes must remain backward compatible within the same major version.
- Major version is represented in the URL path (for example, `/api/v1/...`).

## Compatibility Rules

### Backward-compatible changes (allowed in current major)

- Add optional request fields.
- Add response fields that clients can ignore.
- Add new endpoints/resources.
- Broaden enum support only when old values remain valid.

### Breaking changes (require new major)

- Remove or rename endpoints.
- Remove or rename request/response fields.
- Change field types or semantics incompatibly.
- Tighten validation in ways that reject previously valid requests.
- Change authentication or authorization contract incompatibly.

## Contract Source of Truth

- `contracts/openapi/` and `contracts/jsonschema/` are authoritative API contracts.
- Any API behavior change must update the matching contract artifacts in the same PR.
- Any breaking change must include a new major contract and migration guidance.

## Deprecation Policy

- Default minimum deprecation window for public endpoints: **180 days**.
- For high-risk or high-adoption endpoints, use **270 days** unless explicitly waived.
- Deprecation notice must include:
  - Affected endpoint(s)/field(s)
  - Replacement endpoint(s)/field(s)
  - Deprecation start date (UTC)
  - Sunset date (UTC)
  - Migration guide link

## Sunset Process

1. **Proposal**
   - Open API change proposal with compatibility classification (non-breaking vs breaking).
2. **Announcement**
   - Publish deprecation notice in release notes and API docs.
3. **Transition**
   - Maintain old and new behavior during deprecation window.
   - Monitor usage and contact known consumers where possible.
4. **Readiness Review**
   - Confirm migration guidance and telemetry indicate acceptable readiness.
5. **Sunset Execution**
   - Remove deprecated behavior only after published sunset date.
6. **Post-sunset Validation**
   - Verify no unexpected critical consumer impact.

## Exception Handling

Emergency exceptions (for security or compliance) may shorten windows only when:

- Security leadership approves exception in writing.
- Compensating communication plan is published.
- Incident or risk reference is attached to the release.

## Enforcement in PRs

PRs that change API contracts or behavior must include:

- Compatibility classification
- Deprecation/sunset dates when applicable
- Migration notes and impacted consumers
- Updated contracts and docs

Use the repository PR template checklist to attest compliance.
