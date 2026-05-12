# Legacy debt baseline overrides

CI enforces staged legacy debt thresholds for legacy markers and legacy directories.

- Markers scanned: `DEPRECATED`, `OBSOLETE`
- Directories scanned: configured in `config/ci/legacy_debt_config.json`

The gate fails when counts exceed the effective threshold. Effective threshold is the minimum of:

1. Baseline + temporary explicit approval (`allowed_increase`)
2. Active staged threshold for today's date from `staged_thresholds`

## Staged threshold policy

Use `config/ci/legacy_debt_approvals.json` to encode release-over-release target reductions.

- Configure `staged_thresholds.<category>[]` entries with:
  - `effective_on` (`YYYY-MM-DD`)
  - `max_count`
- Add stages in chronological order.
- Each new stage should reduce or hold counts relative to the previous stage.

## Temporary override process

Use `config/ci/legacy_debt_approvals.json`.

1. Update the target category (`DEPRECATED`, `OBSOLETE`, or `legacy_directories`).
2. Set:
   - `allowed_increase`
   - `expires_on` (`YYYY-MM-DD`)
   - `owner`
   - `reason`
3. Include a cleanup ticket and target removal date in your PR.
4. Reset `allowed_increase` to `0` after cleanup.

## Obsolete marker approval metadata requirements

For each entry in `obsolete_marker_approvals`, CI requires:

- `owner`
- `target_removal_date` (`YYYY-MM-DD`)

CI fails if either field is missing or the target removal date is invalid.

## Local command

```bash
python scripts/ci/check_legacy_debt.py \
  --baseline config/ci/legacy_debt_baseline.json \
  --approvals config/ci/legacy_debt_approvals.json \
  --config config/ci/legacy_debt_config.json \
  --write-report artifacts/legacy-debt-report.json
```

The output includes `file:line` entries for fast remediation.
