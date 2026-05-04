# Validation Program Initial Failure Classification

The first focused P0 validation execution was intentionally run before fixing application or fixture gaps. The run discovered the new validation suites correctly and started 42 P0 tests, but the broad run was stopped after repeated 30-second route assertion failures because the failure signature was systemic rather than isolated.

| Evidence | Finding | Classification | Resolution Status |
|---|---|---|---|
| `/home/ubuntu/terminal_full_output/2026-05-03_20-38-14_574744_207319.txt` | Protected validation routes redirected to `http://localhost:3001/login` despite using the shared `authedPage` fixture. | Test harness/auth fixture drift caused by the application's migration to cookie-era `sessionStorage` metadata. | Fixed in `e2e/fixtures/auth-helpers.ts` by seeding `vf.auth.session.meta` and reloading so `AuthProvider` observes the seeded session. |
| `/home/ubuntu/terminal_full_output/2026-05-03_20-39-41_101709_207508.txt` | A single export validation test failed because expected business-case UI evidence was searched on the login page. | Same systemic auth fixture failure, not a deliverable UI gap. | Re-run passed after the auth fixture fix. |
| `single_validation_after_auth_fix` shell evidence | `e2e/export-workflows.spec.ts -g "approved business case exposes final PDF"` passed in 4.0 seconds. | Confirms the shared authenticated route setup now reaches protected pages. | Verified. |

The initial failure classification is important because it prevents a false product-readiness conclusion. The first red state showed that the executable validation program itself had correctly caught an authentication harness regression before the route-level workflow contracts could produce meaningful product gaps.
