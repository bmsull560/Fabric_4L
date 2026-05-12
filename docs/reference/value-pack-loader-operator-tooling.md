# Value Pack Loader Script (Non-Production Operator Tooling)

`scripts/load_value_packs.py` is **non-production operator tooling** for local validation/loading workflows.

## Execution contract

### Inputs
- `--pack <pack_id>`: process one pack from `packs/pack-manifest.json`.
- `--all`: process all packs from the manifest.
- `--dry-run`: validate/transform without loading.
- `--validate`: validation-only mode (internally uses dry-run behavior).
- `--api-url <url>`: base URL for Layer 3 API target.
- `--non-prod` (**required**): explicit acknowledgement that this script is non-production-only.

### Environment variables
- `RELEASE_PIPELINE`:
  - If set to `1`, `true`, or `yes`, script exits with code `2`.
  - This blocks use in release pipeline contexts.

### Authentication / tenant scope
- This script currently performs validation + transform flows and does **not** perform authenticated API writes.
- Because there is no authenticated tenant context in this script, it must not be used for production data mutation paths.

### Outputs
- Prints per-pack validation/transform status to stdout.
- Returns non-zero exit status for invalid usage or pack validation errors.
- Status objects contain one of:
  - `success`
  - `error` (with `errors[]`)
  - `dry_run`

## Safe usage examples

```bash
python scripts/load_value_packs.py --non-prod --all --dry-run
python scripts/load_value_packs.py --non-prod --pack financial-services-v1 --dry-run
```

## Guardrails
- Mandatory `--non-prod` acknowledgement.
- Hard block when `RELEASE_PIPELINE` indicates release execution.
- Payload validation surfaces structured errors for malformed formulas/variables.
