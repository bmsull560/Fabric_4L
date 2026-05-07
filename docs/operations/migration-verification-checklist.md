# Migration verification checklist

Run from repository root:

```bash
scripts/verification/migration_verification_checklist.sh
```

## Expected output

- Step `[1/4]` prints:
  - `PASS: no legacy \`value-fabric/\` filesystem references found in active code/config.`
- Step `[2/4]` prints a `REPO HYGIENE REPORT` with `Status     : PASS`.
- Step `[3/4]` prints no matches for actionable code/config in `services/`, `scripts/`, and `tests/`.
- Step `[4/4]` prints:
  - `PASS: compatibility namespace imports resolve`

If any step fails, treat as migration regression and block merge until fixed.
