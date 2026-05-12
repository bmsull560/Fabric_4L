<#
.SYNOPSIS
    Run Playwright E2E tests inside Docker for the Value Fabric frontend.

.DESCRIPTION
    Builds and runs the Playwright test container with live source mounting.
    Supports headless, headed, and Playwright UI mode on Windows hosts.

.PARAMETER Build
    Build or rebuild the Docker image. Do this after changing dependencies.

.PARAMETER TestProject
    Playwright project to run (contracts, journeys, backend-integrated, etc.).
    Default: contracts

.PARAMETER UiMode
    Launch Playwright UI mode (interactive web UI on http://localhost:9323).

.PARAMETER Headed
    Run tests in headed mode (requires X11/VNC; limited support on Windows Docker).
    Most users should use -UiMode instead for interactive debugging.

.PARAMETER BackendUrl
    URL of the backend API for backend-integrated tests.
    Example: http://host.docker.internal:8004

.PARAMETER FrontendUrl
    URL of the frontend under test.
    Default: http://localhost:3001

.PARAMETER ExtraArgs
    Additional arguments passed to the Playwright CLI.

.EXAMPLE
    .\scripts\run-playwright-docker.ps1 -Build

.EXAMPLE
    .\scripts\run-playwright-docker.ps1 -TestProject contracts

.EXAMPLE
    .\scripts\run-playwright-docker.ps1 -TestProject backend-integrated -BackendUrl http://host.docker.internal:8004

.EXAMPLE
    .\scripts\run-playwright-docker.ps1 -TestProject contracts -UiMode
#>
param(
    [switch]$Build,
    [string]$TestProject = "contracts",
    [switch]$UiMode,
    [switch]$Headed,
    [string]$BackendUrl = "",
    [string]$FrontendUrl = "",
    [string]$ExtraArgs = ""
)

$ErrorActionPreference = "Stop"
$ComposeFile = [System.IO.Path]::Combine($PSScriptRoot, "..", "docker-compose.playwright.yml")

# Verify Docker Desktop is responsive
try {
    docker info | Out-Null
} catch {
    Write-Error "Docker does not appear to be running. Please start Docker Desktop and try again."
    exit 1
}

# Build image if requested
if ($Build) {
    Write-Host "=== Building Playwright Docker image ===" -ForegroundColor Cyan
    docker compose -f $ComposeFile build playwright
    Write-Host "=== Build complete ===" -ForegroundColor Green
    return
}

# Prepare environment variables for docker compose
$env:PLAYWRIGHT_BASE_URL = if ($FrontendUrl) { $FrontendUrl } else { "http://localhost:3001" }
if ($BackendUrl) { $env:PLAYWRIGHT_BACKEND_URL = $BackendUrl }

# Construct the command to run inside the container
$PlaywrightCmd = "pnpm exec playwright test --project=$TestProject"
if ($UiMode) {
    $PlaywrightCmd += " --ui-host=0.0.0.0 --ui-port=9323"
} elseif ($Headed) {
    $PlaywrightCmd += " --headed"
}
if ($ExtraArgs) {
    $PlaywrightCmd += " $ExtraArgs"
}

Write-Host ""
Write-Host "=== Running Playwright in Docker ===" -ForegroundColor Cyan
Write-Host "Project    : $TestProject"
Write-Host "Frontend   : $($env:PLAYWRIGHT_BASE_URL)"
if ($BackendUrl) { Write-Host "Backend    : $BackendUrl" }
Write-Host "Command    : $PlaywrightCmd"
Write-Host ""

# Run the container (--service-ports exposes compose ports for UI mode)
docker compose -f $ComposeFile run --rm --service-ports playwright sh -c "$PlaywrightCmd"

$ExitCode = $LASTEXITCODE

Write-Host ""
if ($ExitCode -eq 0) {
    Write-Host "=== Tests passed ===" -ForegroundColor Green
} else {
    Write-Host "=== Tests failed (exit code $ExitCode) ===" -ForegroundColor Red
}

# Print result locations
$ReportPath = [System.IO.Path]::Combine($PSScriptRoot, "..", "playwright-report", "index.html")
$JunitPath  = [System.IO.Path]::Combine($PSScriptRoot, "..", "e2e-results", "junit.xml")

Write-Host ""
Write-Host "Results:" -ForegroundColor Cyan
if (Test-Path $ReportPath) {
    Write-Host "  HTML Report : $ReportPath"
}
if (Test-Path $JunitPath) {
    Write-Host "  JUnit XML   : $JunitPath"
}
Write-Host ""

exit $ExitCode
