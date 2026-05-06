# bootstrap-dev.ps1 — Local developer onboarding for Infisical-managed secrets (Windows).
#
# Prerequisites:
#   1. Install the Infisical CLI: https://infisical.com/docs/cli/overview
#   2. Have access to the fabric-4l Infisical project
#
# Usage:
#   .\scripts\infisical\bootstrap-dev.ps1

$ErrorActionPreference = "Stop"

Write-Host "`n🔐 Value Fabric — Infisical Bootstrap (Dev)" -ForegroundColor Cyan
Write-Host "=============================================`n"

# ── Step 1: Check Infisical CLI ──────────────────────────────────────────────
$infisicalPath = Get-Command infisical -ErrorAction SilentlyContinue
if (-not $infisicalPath) {
    Write-Host "✗ Infisical CLI not found." -ForegroundColor Red
    Write-Host "  Install it from: https://infisical.com/docs/cli/overview"
    Write-Host ""
    Write-Host "  Windows (scoop): scoop bucket add org https://github.com/nicholasgasior/scoop-bucket && scoop install infisical"
    Write-Host "  Windows (choco): choco install infisical"
    exit 1
}
$version = & infisical --version 2>$null
Write-Host "✓ Infisical CLI found: $version" -ForegroundColor Green

# ── Step 2: Check login ─────────────────────────────────────────────────────
Write-Host "`nChecking Infisical authentication..."
$userInfo = & infisical user 2>$null
if ($userInfo -notmatch "email") {
    Write-Host "⚠ Not logged in. Running 'infisical login'..." -ForegroundColor Yellow
    & infisical login
}
Write-Host "✓ Authenticated with Infisical" -ForegroundColor Green

# ── Step 3: Verify project paths ────────────────────────────────────────────
Write-Host "`nVerifying secret paths exist..."
$paths = @(
    "/fabric-4l/value-fabric/dev",
    "/fabric-4l/apps/web/dev"
)

foreach ($p in $paths) {
    try {
        & infisical secrets --env=dev --path=$p --silent 2>$null
        Write-Host "  ✓ $p" -ForegroundColor Green
    }
    catch {
        Write-Host "  ⚠ $p — path not found or no access" -ForegroundColor Yellow
    }
}

# ── Step 4: Print usage ─────────────────────────────────────────────────────
Write-Host "`n============================================="
Write-Host "Ready! Run services with Infisical-injected secrets:" -ForegroundColor Green
Write-Host ""
Write-Host "  # Backend"
Write-Host "  infisical run --env=dev --path=/fabric-4l/value-fabric/dev -- pnpm --dir value-fabric dev"
Write-Host ""
Write-Host "  # Frontend"
Write-Host "  infisical run --env=dev --path=/fabric-4l/apps/web/dev -- pnpm --dir apps/web dev"
Write-Host ""
Write-Host "  # Or use package scripts:"
Write-Host "  pnpm dev:backend"
Write-Host "  pnpm dev:frontend"
Write-Host ""
