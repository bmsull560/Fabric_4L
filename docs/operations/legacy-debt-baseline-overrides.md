# Legacy debt baseline overrides

CI now enforces a baseline for legacy markers and legacy directories.

- Markers scanned: `DEPRECATED`, `OBSOLETE`
- Directories scanned: configured in `config/ci/legacy_debt_config.json`

The gate fails when counts exceed `config/ci/legacy_debt_baseline.json` unless there is an unexpired explicit approval.

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

## Local command

```bash
python scripts/ci/check_legacy_debt.py \
  --baseline config/ci/legacy_debt_baseline.json \
  --approvals config/ci/legacy_debt_approvals.json \
  --config config/ci/legacy_debt_config.json \
  --write-report artifacts/legacy-debt-report.json
```

The output includes `file:line` entries for fast remediation.
