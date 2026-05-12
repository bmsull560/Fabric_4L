# Repro Seed Anonymization Contract

All seed packs MUST satisfy this contract before commit.

## Required scrubbing scope

Scrub the following fields everywhere they appear (payloads, metadata, logs, snapshots, embedded JSON strings):

- Direct identifiers: names, emails, phone numbers, physical addresses, account IDs, API keys.
- Indirect identifiers: hostnames, internal URLs, document titles containing customer identity, free text with named entities.
- Sensitive operational details: secrets, tokens, auth headers, signed URLs.

## Deterministic replacement rules

1. Replace each sensitive value with a deterministic token using a stable mapping table scoped to one seed pack.
2. Deterministic token format:
   - Person: `person_<N>`
   - Organization: `org_<N>`
   - Email: `email_<N>@example.invalid`
   - Document/record IDs: `rec_<N>`
3. Keep 1:1 mapping within a pack so foreign-key and cross-record references remain valid.
4. Never reuse real tenant identifiers. Use canonical synthetic IDs (`tenant_alpha`, `tenant_beta`, ...).
5. Never derive tokens from unhashed source values in committed artifacts.

## Relational integrity requirements

- Parent/child references must continue to resolve after scrubbing.
- Join keys must be preserved through token mapping.
- Event chronology fields needed for incident reproduction must remain internally consistent.
- Cross-tenant references are forbidden unless the incident explicitly reproduces an isolation failure and the pack documents that expected failure in `manifest.json`.

## Required seed-pack files

Each pack must include:

- `manifest.json` (required contract metadata)
- `mapping.json` (deterministic substitutions)
- `payload.json` (anonymized reproducibility fixture)
- `expected-output.json` (runner output pinned for drift detection)

## Validation requirements

Each pack must pass `python scripts/repro-seeds/validate_seed_packs.py`, which verifies deterministic output and tenant-safety invariants in CI.
