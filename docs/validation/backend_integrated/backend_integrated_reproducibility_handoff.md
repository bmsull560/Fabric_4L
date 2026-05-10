# Backend-Integrated Reproducibility Handoff

This handoff records how to reproduce the local Docker-backed backend-integrated J1 and J11 evidence bundle. It is an operator and CI/staging handoff, not a production-readiness sign-off.

## Evidence Boundary

This local Docker-backed evidence closes only the local backend-integrated J1+J11 evidence line.

It does not prove:

- production readiness
- paid GA readiness
- CI or staging reproducibility
- SSO/OIDC staging evidence
- live LLM provider evidence
- billing or entitlement evidence
- rollback or restore evidence
- telemetry, dashboard, alerting, or alert receiver evidence
- performance smoke evidence
- Journey SLO evidence
- production-like E2E rehearsal evidence

CI/staging reproduction must be run against the release-candidate SHA and must retain logs, artifacts, redacted environment metadata, and owner sign-off before any broader launch evidence line is closed.

## Required Services

Start the local Docker-backed validation stack with these services:

- `postgres`
- `redis`
- `neo4j`
- `minio`
- `layer1`
- `layer4`
- `frontend`

The local handoff uses `docker-compose.live.yml` plus `.tmp\docker-compose.j11.override.yml`. The override is part of the current local validation setup and must be replaced by an approved CI/staging equivalent before claiming reproducibility outside this workstation.

## Required Environment

Use non-production validation secrets only. Never commit concrete secret values in evidence docs or CI logs.

Required runtime settings:

```powershell
$env:PLAYWRIGHT_BACKEND_URL='http://127.0.0.1:8004'
$env:PLAYWRIGHT_LIVE_MODE='true'
$env:PLAYWRIGHT_LIVE_FRONTEND_URL='http://localhost:3001'
$env:PLAYWRIGHT_BASE_URL='http://localhost:3001'
$env:VITE_USE_MOCKS='false'
$env:VITE_ENABLE_MOCK_FALLBACK='false'
$env:E2E_SEED_DATA='false'
$env:SEED_REPORT_JSON='artifacts/live-workflow-validation/seed-report.json'
Remove-Item Env:\MSW -ErrorAction SilentlyContinue
Remove-Item Env:\MOCKS_ENABLED -ErrorAction SilentlyContinue
```

Required non-production secrets and service settings must match the Docker stack configuration:

- `SERVICE_AUTH_SECRET=<redacted non-production validation secret>`
- `JWT_SECRET=<redacted non-production validation secret>`
- `POSTGRES_PASSWORD=<redacted local validation password>`
- `NEO4J_PASSWORD=<redacted local validation password>`
- `MINIO_ROOT_USER=<redacted local validation user>`
- `MINIO_ROOT_PASSWORD=<redacted local validation password>`

Mock flags must be absent or false. A mock-enabled run is not valid backend-integrated evidence.

## Preferred CI/Staging Runner

Use the dedicated reproducibility runner for CI/staging wiring:

```powershell
python scripts/ci/run_backend_integrated_reproducibility.py --release-candidate-sha <sha> --environment ci
```

The runner starts the Docker-backed validation services unless `--skip-stack-start` is provided, runs the seed guard, runs deterministic seeding, executes J1-only, J11-only, and the J1+J11 pair, verifies the retained seed and JUnit artifacts, detects retry/flaky output, and runs the launch evidence validators. It writes a machine-readable summary to:

```text
artifacts/live-workflow-validation/backend-integrated-reproducibility-summary.json
```

For CI/staging evidence, pass `--environment ci` or `--environment staging` and provide an explicit release-candidate SHA through `--release-candidate-sha`, `RELEASE_CANDIDATE_SHA`, or `GITHUB_SHA`. A local run may fall back to `git rev-parse HEAD`, but the summary is marked `TOOLING_ONLY` and does not close CI/staging reproducibility.

CI evidence additionally requires CI metadata such as `CI=true` or `GITHUB_ACTIONS=true` plus a run identifier such as `GITHUB_RUN_ID`, `CI_PIPELINE_ID`, `BUILD_BUILDID`, or `BUILDKITE_BUILD_ID`.

Staging evidence additionally requires an evidence run identifier and evidence URL through `--evidence-run-id` and `--evidence-url`, or equivalent staging environment variables (`STAGING_EVIDENCE_RUN_ID` / `STAGING_EVIDENCE_URL`, `STAGING_DEPLOYMENT_ID` / `STAGING_DEPLOYMENT_URL`, or `STAGING_RUN_ID` / `STAGING_URL`).

If Playwright reports a retry/flaky result, the runner fails unless `--retry-classification` is provided. A classified retry can be retained as evidence with residual risk, but it is not the same as a clean deterministic PASS.

The script can produce reproducibility evidence, but CI/staging reproducibility remains open until it is executed in the approved CI/staging or production-like environment with:

- release-candidate SHA
- approved CI/staging metadata
- retained artifacts
- logs
- redacted environment metadata
- owner sign-off

The manual commands below remain the fallback for local troubleshooting and for environments that need to run the phases one at a time.

## Reproduction Commands

Run Docker and seed commands from the repository root.

### 1. Start Docker-backed live stack

```powershell
docker compose -f docker-compose.live.yml -f .tmp\docker-compose.j11.override.yml up -d --build --wait postgres redis neo4j minio layer1 layer4 frontend
```

### 2. Verify seed guard

```powershell
node apps/web/scripts/live-env-guard.mjs seed
```

### 3. Seed backend-integrated validation data

```powershell
cmd /c apps\web\node_modules\.bin\tsx.cmd scripts\db\seed-e2e-data.ts --base-url=http://127.0.0.1:8004
```

The seed command must produce `artifacts/live-workflow-validation/seed-report.json` and the report must show:

```text
aggregateStatus=present
requiredRowsPresent=true
```

### 4. Run J1 only

Run Playwright commands from `apps/web` so the local `node_modules\.bin\playwright.cmd` path and `../../artifacts/...` report paths resolve correctly.

```powershell
$env:PLAYWRIGHT_JUNIT_FILE='../../artifacts/live-workflow-validation/playwright/j1-junit.xml'
$env:PLAYWRIGHT_HTML_REPORT='../../artifacts/live-workflow-validation/playwright/j1-html'
$env:PLAYWRIGHT_OUTPUT_DIR='../../artifacts/live-workflow-validation/playwright/j1-test-results'
cmd /c node_modules\.bin\playwright.cmd test --project=backend-integrated e2e/journeys/j1-golden-path-backend-integrated.spec.ts
```

Expected result:

```text
artifacts/live-workflow-validation/playwright/j1-junit.xml
failures=0
errors=0
```

### 5. Run J11 only

```powershell
$env:PLAYWRIGHT_JUNIT_FILE='../../artifacts/live-workflow-validation/playwright/j11-junit.xml'
$env:PLAYWRIGHT_HTML_REPORT='../../artifacts/live-workflow-validation/playwright/j11-html'
$env:PLAYWRIGHT_OUTPUT_DIR='../../artifacts/live-workflow-validation/playwright/j11-test-results'
cmd /c node_modules\.bin\playwright.cmd test --project=backend-integrated e2e/journeys/j11-golden-path-business-lifecycle.spec.ts
```

Expected result:

```text
artifacts/live-workflow-validation/playwright/j11-junit.xml
failures=0
errors=0
```

### 6. Run full J1+J11 pair

```powershell
$env:PLAYWRIGHT_JUNIT_FILE='../../artifacts/live-workflow-validation/playwright/junit.xml'
$env:PLAYWRIGHT_HTML_REPORT='../../artifacts/live-workflow-validation/playwright/html'
$env:PLAYWRIGHT_OUTPUT_DIR='../../artifacts/live-workflow-validation/playwright/test-results'
cmd /c node_modules\.bin\playwright.cmd test --project=backend-integrated e2e/journeys/j1-golden-path-backend-integrated.spec.ts e2e/journeys/j11-golden-path-business-lifecycle.spec.ts
```

Expected result:

```text
artifacts/live-workflow-validation/playwright/junit.xml
tests=20
failures=0
errors=0
```

### 7. Validate launch evidence guards

Run from the repository root:

```powershell
python scripts/ci/validate_core_ga_launch_evidence.py
python scripts/ci/validate_final_testing_launch_gate.py
```

## Expected Artifact Bundle

| Artifact | Required validation |
|---|---|
| `artifacts/live-workflow-validation/seed-report.json` | `aggregateStatus=present`, `requiredRowsPresent=true` |
| `artifacts/live-workflow-validation/playwright/j1-junit.xml` | `failures=0`, `errors=0` |
| `artifacts/live-workflow-validation/playwright/j11-junit.xml` | `failures=0`, `errors=0` |
| `artifacts/live-workflow-validation/playwright/junit.xml` | `tests=20`, `failures=0`, `errors=0` |
| `artifacts/live-workflow-validation/playwright/j1-html` | Retained J1 HTML report |
| `artifacts/live-workflow-validation/playwright/j11-html` | Retained J11 HTML report |
| `artifacts/live-workflow-validation/playwright/html` | Retained pair HTML report |
| `artifacts/live-workflow-validation/playwright/j1-test-results` | Retained J1 traces, screenshots, and results |
| `artifacts/live-workflow-validation/playwright/j11-test-results` | Retained J11 traces, screenshots, and results |
| `artifacts/live-workflow-validation/playwright/test-results` | Retained pair traces, screenshots, and results |

## CI/Staging Evidence Attachment Requirements

A CI or staging reproduction is valid only when the evidence bundle includes:

- release-candidate commit SHA
- exact command sequence or CI job URL
- approved CI/staging run identifier and evidence URL or job URL
- retained seed report
- retained J1, J11, and J1+J11 JUnit XML artifacts
- JUnit results with `failures=0`, `errors=0`, `skipped=0`, and pair `tests=20`
- retry/flaky status showing no retries, or explicit retry classification with residual risk
- retained Playwright HTML and test-results directories
- Docker compose or staging deployment service health output
- sanitized frontend, Layer 1, and Layer 4 logs for the validation window
- redacted environment manifest showing mock flags disabled and required live URLs configured
- owner sign-off for the environment and artifact bundle

Do not update launch docs or blocker registers to close CI/staging reproducibility until these artifacts exist for the release-candidate SHA.

## Still Open After Local PASS

The following evidence remains open after a local Docker-backed J1+J11 PASS:

- CI/staging reproducibility
- Journey SLO report
- live LLM provider evidence
- SSO/OIDC evidence
- billing evidence and paid GA readiness
- rollback/restore evidence
- telemetry, dashboards, alerting, and alert receiver evidence
- performance smoke evidence
- production-like E2E rehearsal
- broad security suite CI artifact, if required by release policy
- frontend timing artifact, if required by release policy

Production readiness remains unproven and paid GA remains blocked until all required launch evidence exists and is reproducible in the approved environment.
