# Billing & Entitlements Regression Pack

This pack encodes regression protections for launch-readiness review on:

1. Plan/entitlement enforcement per tenant + region.
2. Feature-flag interactions with entitlement limits.
3. Billing-impacting behavior (upgrade/downgrade, metering, overage).
4. Contract checks for entitlement/billing APIs if those endpoints are exposed in `contracts/openapi/*.json`.

CI runs this suite in `.github/workflows/pr-checks.yml` under the
`billing-entitlements-regression` job and publishes release-evidence artifacts:

- `billing-entitlements-summary.json`
- `billing-entitlements-summary.md`

These artifacts are intended to be consumed during launch checklist reviews.
