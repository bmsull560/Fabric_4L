# Playwright Docker Live Testing Guide

This guide explains how to run the Value Fabric frontend Playwright E2E tests inside Docker on a Windows host. The setup supports live code editing, headless and UI-headed execution, and surfaces test results back to the host filesystem.

## Prerequisites

- **Docker Desktop** for Windows (WSL2 backend recommended)
- **PowerShell** 5.1 or later (PowerShell 7+ preferred)
- At least **8 GB RAM** allocated to Docker (Playwright + browsers are memory-intensive)

## Files Added

| File | Purpose |
|------|---------|
| `apps/web/Dockerfile.playwright` | Docker image with Node 22, pnpm, and Playwright browsers |
| `docker-compose.playwright.yml` | Orchestrates the test container with volume mounts |
| `apps/web/scripts/playwright-docker-entrypoint.sh` | Entrypoint that seeds `node_modules` into the named volume |
| `scripts/run-playwright-docker.ps1` | PowerShell helper to build, run, and debug tests |

## Quick Start

### 1. Build the Docker image

```powershell
.\scripts\run-playwright-docker.ps1 -Build
```

> **Note:** Re-run `-Build` whenever you change `package.json`, `pnpm-lock.yaml`, or need to refresh dependencies.

### 2. Run contract tests (headless, no backend)

```powershell
.\scripts\run-playwright-docker.ps1 -TestProject contracts
```

This starts the container, seeds `node_modules`, runs the fast mocked contract tests, and writes results to:
- `playwright-report/index.html`
- `e2e-results/junit.xml`

### 3. Open the HTML report

```powershell
# On the host — Playwright's trace viewer
npx playwright show-report playwright-report
```

Or simply open `playwright-report/index.html` in your browser.

## Live Code Changes

The `apps/web/` directory is bind-mounted into the container. Any change you make on the host is visible immediately inside the container. Re-run the PowerShell script to execute tests against the updated code.

> **Tip:** The `node_modules` directory is stored in a Docker named volume (`playwright_node_modules`) rather than being mounted from the host. This prevents OS binary mismatches (Windows vs. Linux).

## Test Projects

The frontend already defines several Playwright projects in `playwright.config.ts`:

| Project | Description | Backend Required |
|---------|-------------|------------------|
| `contracts` | Fast mocked page-level tests | No |
| `journeys` | Chained user workflow tests | No (mocked) |
| `backend-integrated` | Tests tagged `@backend` | Yes |
| `contracts-firefox` | Cross-browser contract tests | No |
| `contracts-webkit` | Cross-browser contract tests | No |

Run any project with:

```powershell
.\scripts\run-playwright-docker.ps1 -TestProject <project-name>
```

## Backend-Integrated Tests

Some journeys require a live backend. Use the deterministic E2E backend stack:

```powershell
# 1. Start the backend services (postgres, redis, neo4j, layer4)
docker compose -f docker-compose.e2e.yml up -d --wait

# 2. Seed deterministic test data
#    (run from host if you have Node/pnpm, or skip if already seeded)

# 3. Run backend-integrated tests
.\scripts\run-playwright-docker.ps1 `
  -TestProject backend-integrated `
  -BackendUrl http://host.docker.internal:8004

# 4. Tear down backend when done
docker compose -f docker-compose.e2e.yml down -v
```

## Interactive / Headed Modes

### UI Mode (Recommended for debugging)

Playwright UI mode starts a web server you can access from your host browser:

```powershell
.\scripts\run-playwright-docker.ps1 -TestProject contracts -UiMode
```

Then open **http://localhost:9323** in your browser.

### Headed Mode (Limited on Windows Docker)

Headed mode opens native browser windows. On Windows Docker Desktop this requires an X server (e.g., VcXsrv) and is generally not recommended. Use **UI Mode** instead.

```powershell
# Only if you have an X server configured
.\scripts\run-playwright-docker.ps1 -TestProject contracts -Headed
```

## Passing Extra Arguments

You can pass arbitrary flags to the Playwright CLI:

```powershell
# Run a single test file
.\scripts\run-playwright-docker.ps1 -TestProject contracts -ExtraArgs "e2e/contracts/admin.spec.ts"

# Run with verbose output
.\scripts\run-playwright-docker.ps1 -TestProject contracts -ExtraArgs "--debug"

# Update snapshots
.\scripts\run-playwright-docker.ps1 -TestProject contracts -ExtraArgs "--update-snapshots"
```

## Manual Docker Compose Commands

If you prefer running docker compose directly instead of the PowerShell helper:

```powershell
# Build
docker compose -f docker-compose.playwright.yml build

# Run contract tests
docker compose -f docker-compose.playwright.yml run --rm playwright `
  sh -c "pnpm exec playwright test --project=contracts"

# Run with UI mode (expose port)
docker compose -f docker-compose.playwright.yml run --rm --service-ports playwright `
  sh -c "pnpm exec playwright test --project=contracts --ui-host=0.0.0.0 --ui-port=9323"

# Run against a custom frontend URL
docker compose -f docker-compose.playwright.yml run --rm playwright `
  sh -c "PLAYWRIGHT_BASE_URL=http://host.docker.internal:3001 pnpm exec playwright test --project=contracts"
```

## Test Results

After every run, the following directories on the **host** contain the outputs:

| Path | Content |
|------|---------|
| `./playwright-report/` | Interactive HTML report (`index.html`) |
| `./e2e-results/` | JUnit XML, traces, screenshots, and videos |

These paths are already listed in `.gitignore` and will not be committed.

## Troubleshooting

### Container fails to start with "pnpm: command not found"

The entrypoint re-activates corepack on every start. If this fails, rebuild the image:

```powershell
.\scripts\run-playwright-docker.ps1 -Build
```

### Tests fail because a new dependency was added

The named volume may contain stale `node_modules`. Rebuild the image to bake the new dependencies:

```powershell
.\scripts\run-playwright-docker.ps1 -Build
```

Or force a fresh volume:

```powershell
docker compose -f docker-compose.playwright.yml down -v
.\scripts\run-playwright-docker.ps1 -Build
```

### Backend-integrated tests cannot reach the API

Ensure the backend is running and accessible from the container:

```powershell
# Test connectivity from inside the container
docker compose -f docker-compose.playwright.yml run --rm playwright `
  sh -c "curl -s http://host.docker.internal:8004/health"
```

If using `docker-compose.e2e.yml`, verify the services are healthy:

```powershell
docker compose -f docker-compose.e2e.yml ps
```

### Port 9323 already in use

Another process or container is using the UI mode port. Either stop the other process or map a different port in `docker-compose.playwright.yml`.

### Windows Defender / antivirus slows bind mounts

Exclude the repository directory from real-time scanning if file I/O inside the container feels sluggish.

## Architecture Notes

- **Image base:** `mcr.microsoft.com/playwright:v1.47.0-jammy` — guarantees all browsers and system libraries are present.
- **Node upgrade:** NodeSource Node 22 is layered on top because the base image ships Node 20.
- **Workspace isolation:** `eslint-plugin-fabric-contracts` (a monorepo workspace dependency) is stripped during the image build. It is not needed at runtime for E2E tests.
- **Volume strategy:** The bind mount gives live source access; the named volume gives Linux-native `node_modules` without corrupting the host's copy.
