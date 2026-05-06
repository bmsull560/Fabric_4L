# setup-gemini-cli.ps1
# Professional Gemini CLI setup for Windows PowerShell
# Run from PowerShell 7+:
#   Set-ExecutionPolicy -Scope Process Bypass -Force
#   .\setup-gemini-cli.ps1

[CmdletBinding()]
param(
    [switch]$InstallNodeWithWinget,
    [switch]$UsePreview,
    [switch]$UseNightly,
    [switch]$CreateGlobalGeminiMd = $true,
    [switch]$CreateProjectGeminiMd = $true
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "OK: $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "WARN: $Message" -ForegroundColor Yellow
}

function Assert-Command {
    param(
        [string]$Name,
        [string]$InstallHint
    )

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        throw "$Name was not found. $InstallHint"
    }

    return $cmd.Source
}

function Get-NodeMajorVersion {
    $versionText = node --version
    if ($versionText -notmatch '^v?(\d+)\.') {
        throw "Could not parse Node.js version: $versionText"
    }
    return [int]$Matches[1]
}

Write-Step "Checking PowerShell version"
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Warn "PowerShell 7+ is recommended. Current: $($PSVersionTable.PSVersion)"
} else {
    Write-Ok "PowerShell $($PSVersionTable.PSVersion)"
}

Write-Step "Checking Node.js and npm"

$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue

if ((-not $nodeCmd -or -not $npmCmd) -and $InstallNodeWithWinget) {
    Write-Step "Installing Node.js LTS using winget"
    Assert-Command winget "Install winget/App Installer from Microsoft Store, or install Node manually."
    winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
    Write-Warn "Restart PowerShell after Node installation if node/npm are still not found."
}

$nodePath = Assert-Command node "Install Node.js LTS from https://nodejs.org or rerun with -InstallNodeWithWinget."
$npmPath  = Assert-Command npm  "Install Node.js LTS from https://nodejs.org or rerun with -InstallNodeWithWinget."

Write-Ok "node: $nodePath"
Write-Ok "npm:  $npmPath"

$nodeMajor = Get-NodeMajorVersion
if ($nodeMajor -lt 18) {
    throw "Gemini CLI requires a modern Node.js runtime. Upgrade to Node.js 18+ or preferably current LTS. Current: $(node --version)"
}
Write-Ok "Node.js version: $(node --version)"
Write-Ok "npm version: $(npm --version)"

Write-Step "Checking npm global prefix"
$npmPrefix = npm config get prefix
Write-Ok "npm global prefix: $npmPrefix"

# Add common npm global bin path to current process PATH if needed.
$possibleBins = @(
    $npmPrefix,
    (Join-Path $env:APPDATA "npm")
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

foreach ($bin in $possibleBins) {
    if ($env:Path -notlike "*$bin*") {
        $env:Path = "$bin;$env:Path"
    }
}

Write-Step "Selecting Gemini CLI release channel"

if ($UsePreview -and $UseNightly) {
    throw "Choose either -UsePreview or -UseNightly, not both."
}

$package = "@google/gemini-cli"
if ($UsePreview) {
    $package = "@google/gemini-cli@preview"
    Write-Warn "Using preview channel. This may contain regressions."
} elseif ($UseNightly) {
    $package = "@google/gemini-cli@nightly"
    Write-Warn "Using nightly channel. This may be unstable."
} else {
    $package = "@google/gemini-cli@latest"
}

Write-Step "Installing official Gemini CLI package: $package"
Write-Warn "Security note: only installing the official scoped npm package '@google/gemini-cli'. Avoid unscoped or 'early-access' Gemini CLI installers."

npm install -g $package

Write-Step "Verifying Gemini CLI installation"
$geminiCmd = Get-Command gemini -ErrorAction SilentlyContinue

if (-not $geminiCmd) {
    Write-Warn "gemini command was not found in PATH after install."
    Write-Warn "Try opening a new PowerShell window, then run: gemini --version"
} else {
    Write-Ok "gemini: $($geminiCmd.Source)"
    try {
        gemini --version
    } catch {
        Write-Warn "Gemini CLI installed, but version command returned an error: $($_.Exception.Message)"
    }
}

Write-Step "Creating Gemini CLI directories"

$globalGeminiDir = Join-Path $HOME ".gemini"
$globalGeminiMd  = Join-Path $globalGeminiDir "GEMINI.md"

New-Item -ItemType Directory -Force -Path $globalGeminiDir | Out-Null
Write-Ok "Global Gemini directory: $globalGeminiDir"

if ($CreateGlobalGeminiMd -and -not (Test-Path $globalGeminiMd)) {
@"
# Global Gemini CLI Instructions

You are assisting a senior full-stack engineer.

Default operating rules:
- Inspect the repository before making changes.
- Prefer small, reviewable patches.
- Do not invent files, scripts, or APIs.
- Run the narrowest relevant validation first.
- Never manually edit generated files.
- Preserve security boundaries, tenant isolation, and contract tests.
- Explain assumptions and risks clearly.
- For production code, avoid fake data, hardcoded secrets, no-op safety checks, and silent fallbacks.

Coding preferences:
- TypeScript: strict types, no `any`, domain models separated from DTOs.
- Python: typed functions, Pydantic/FastAPI contracts, explicit errors.
- Tests: add characterization tests before refactoring risky logic.
- CI: prefer checks that catch drift before runtime.
"@ | Set-Content -Path $globalGeminiMd -Encoding UTF8

    Write-Ok "Created global GEMINI.md: $globalGeminiMd"
} elseif ($CreateGlobalGeminiMd) {
    Write-Ok "Global GEMINI.md already exists: $globalGeminiMd"
}

if ($CreateProjectGeminiMd) {
    $projectGeminiMd = Join-Path (Get-Location) "GEMINI.md"

    if (-not (Test-Path $projectGeminiMd)) {
@"
# Project Instructions for Gemini CLI

## Project Context

This repository should be treated as production-grade software.

Before editing:
- Read the relevant files.
- Identify existing conventions.
- Search for tests.
- Prefer compatibility-preserving changes.
- Avoid broad rewrites.

## Architecture Rules

- Respect existing module boundaries.
- Do not introduce new dependencies without justification.
- Do not edit generated files manually.
- Do not return fake production data.
- Do not add hardcoded secrets.
- Do not create no-op security or safety implementations.
- Fail closed for security, tenant isolation, money, workflow, and governance paths.

## Frontend Rules

- React components should consume domain/view models, not raw API DTOs.
- Keep DTO-to-domain mapping in adapters.
- Validate network responses before using them.
- Avoid `any`.

## Backend Rules

- FastAPI routes should use explicit request/response models.
- Pydantic DTOs define API contracts.
- Use clear HTTP errors instead of silent fallback behavior.
- Preserve trace IDs, tenant IDs, and audit metadata.

## Execution Style

For each task:
1. Inspect.
2. Plan briefly.
3. Patch narrowly.
4. Test.
5. Report changed files, validation run, and remaining risks.
"@ | Set-Content -Path $projectGeminiMd -Encoding UTF8

        Write-Ok "Created project GEMINI.md: $projectGeminiMd"
    } else {
        Write-Ok "Project GEMINI.md already exists: $projectGeminiMd"
    }
}

Write-Step "Optional authentication notes"
Write-Host @"

Gemini CLI is installed.

Next steps:
1. Open a new PowerShell terminal if 'gemini' is not recognized.
2. Run:
   gemini
3. Follow the interactive authentication flow.

For API-key based workflows, use your provider's official docs and store secrets in environment variables or a secret manager.
Do not paste API keys into GEMINI.md, source files, or shell history.

Useful commands:
  gemini --version
  gemini --help
  gemini

Security reminder:
  Install only '@google/gemini-cli' from npm or official Google/Gemini CLI docs.
  Avoid random PowerShell curl/install commands for Gemini CLI.

"@ -ForegroundColor White

Write-Ok "Gemini CLI setup complete."
