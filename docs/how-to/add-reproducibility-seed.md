# How to add a reproducibility seed pack for a production incident

Use this workflow whenever a production bug requires a deterministic local reproduction artifact.

## Canonical paths

- Tooling: `scripts/repro-seeds/`
- Seed packs: `tests/repro-seeds/packs/<seed_id>/`

## Step 1: Create the seed pack directory

Create a folder named with the `seed_id` pattern `seed-<scope>-<incident>`.

Required files:

- `manifest.json`
- `mapping.json`
- `payload.json`
- `expected-output.json`

## Step 2: Fill the manifest contract

Populate `manifest.json` with:

- `seed_id`
- `source_incident_ticket`
- `affected_layers`
- `required_migration_revision`
- `deterministic_rng_seed`
- `anonymization_profile`
- `tenant_scope`

Validate against `scripts/repro-seeds/manifest.schema.json`.

## Step 3: Apply strict anonymization

Follow `scripts/repro-seeds/anonymization-contract.md`:

- scrub direct + indirect identifiers
- maintain deterministic mapping in `mapping.json`
- preserve relational integrity across joins/foreign keys
- never include real tenant identifiers

## Step 4: Generate and pin expected output

Run the runner once and copy the applied output into `expected-output.json`:

```bash
python scripts/repro-seeds/runner.py \
  --pack-dir tests/repro-seeds/packs/<seed_id> \
  --migration-revision <required_migration_revision> \
  --output-dir /tmp/repro-seed-output
cp /tmp/repro-seed-output/<seed_id>.applied.json \
  tests/repro-seeds/packs/<seed_id>/expected-output.json
```

This creates a stable regression artifact used by CI drift checks.

## Step 5: Verify deterministic replay and tenant safety

Run:

```bash
python scripts/repro-seeds/validate_seed_packs.py
```

This enforces:

- required manifest fields
- deterministic output (hash stable across repeated runs)
- exact expected-output match
- tenant-scope assertions
- payload scrub checks

## Step 6: Replay one seed after migration to target revision

Run:

```bash
python scripts/repro-seeds/runner.py \
  --pack-dir tests/repro-seeds/packs/<seed_id> \
  --migration-revision <required_migration_revision> \
  --migrate-cmd "alembic upgrade {revision}" \
  --output-dir /tmp/repro-seed-output
```

If revision mismatches, runner fails closed before applying payload.

## CI gate

CI runs `.github/workflows/repro-seed-validation.yml` on PRs and pushes.
