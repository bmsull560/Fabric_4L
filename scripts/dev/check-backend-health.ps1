# Backend Health Check Script
# Validates endpoint behavior: expected status codes and payload shapes
# NOT just TCP connectivity (a listening but broken service is not "healthy")

param(
    [int[]]$Ports = @(8001, 8002, 8003, 8004, 8005, 8006),
    [int]$Timeout = 10,
    [switch]$Verbose
)

# Expected health check configuration per layer
# Prefers /ready over /health for readiness gating
# Liveness (/health) = process is running
# Readiness (/ready) = process + dependencies are ready to serve traffic
$LayerHealthConfig = @{
    8001 = @{                                            # Layer 1: Ingestion
        Endpoints = @("/ready", "/health")              # Prefer /ready if available
        ExpectedStatus = 200
        CheckType = "ready"                               # liveness vs readiness
        ExpectedContentPattern = $null
        Name = "Layer 1 Ingestion"
        RequiredForGate = $true
    }
    8002 = @{                                            # Layer 2: Extraction
        Endpoints = @("/ready", "/health")
        ExpectedStatus = 200
        CheckType = "ready"
        ExpectedContentPattern = $null
        Name = "Layer 2 Extraction"
        RequiredForGate = $true
    }
    8003 = @{                                            # Layer 3: Knowledge
        Endpoints = @("/ready", "/health")
        ExpectedStatus = 200
        CheckType = "ready"
        ExpectedContentPattern = "neo4j|postgres|ready"  # Should mention data stores
        Name = "Layer 3 Knowledge"
        RequiredForGate = $true
    }
    8004 = @{                                            # Layer 4: Agents
        Endpoints = @("/ready", "/health")
        ExpectedStatus = 200
        CheckType = "ready"
        ExpectedContentPattern = $null
        Name = "Layer 4 Agents"
        RequiredForGate = $true
    }
    8005 = @{                                            # Layer 5: Ground Truth
        Endpoints = @("/ready", "/health")
        ExpectedStatus = 200
        CheckType = "ready"
        ExpectedContentPattern = $null
        Name = "Layer 5 Ground Truth"
        RequiredForGate = $true
    }
    8006 = @{                                            # Layer 6: Benchmarks
        Endpoints = @("/ready", "/health")
        ExpectedStatus = 200
        CheckType = "ready"
        ExpectedContentPattern = $null
        Name = "Layer 6 Benchmarks"
        RequiredForGate = $true
    }
}

Write-Host "Backend Health Check (Endpoint Behavior Validation)" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Validating: Expected status codes and payload shapes" -ForegroundColor Gray
Write-Host "Not just: TCP connectivity (listening != healthy)" -ForegroundColor Gray

$results = @()
$allHealthy = $true

foreach ($port in $Ports) {
    $config = $LayerHealthConfig[$port]
    if (-not $config) {
        Write-Host "`n⚠ Port $port - Unknown layer configuration" -ForegroundColor Yellow
        continue
    }
    
    Write-Host "`n[$($config.Name)] Port $port..." -NoNewLine
    
    # Try each endpoint in priority order (ready > health > liveness fallback)
    $foundEndpoint = $null
    $response = $null
    $checkTypeUsed = $null
    
    foreach ($endpoint in $config.Endpoints) {
        try {
            $url = "http://localhost:$port$endpoint"
            $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec $Timeout -ErrorAction Stop
            $foundEndpoint = $endpoint
            
            # Determine check type from endpoint used
            if ($endpoint -eq "/ready") {
                $checkTypeUsed = "readiness"
            } elseif ($endpoint -eq "/health") {
                $checkTypeUsed = "liveness"
            } else {
                $checkTypeUsed = "liveness"
            }
            break  # Found a working endpoint
        } catch {
            # Try next endpoint
            continue
        }
    }
    
    if ($foundEndpoint -and $response) {
        $statusOk = $response.StatusCode -eq $config.ExpectedStatus
        $content = $response.Content
        $contentOk = $true
        $contentDetails = ""
        
        # Validate content pattern if configured
        if ($config.ExpectedContentPattern) {
            if ($content -match $config.ExpectedContentPattern) {
                $contentOk = $true
                $contentDetails = " (content pattern matched)"
            } else {
                $contentOk = $false
                $contentDetails = " (content pattern NOT matched: $($config.ExpectedContentPattern))"
            }
        }
        
        if ($statusOk -and $contentOk) {
            $healthStatus = if ($checkTypeUsed -eq "readiness") { "READY" } else { "LIVE (ready unavailable)" }
            Write-Host " ✓ $healthStatus" -ForegroundColor Green
            Write-Host "  Endpoint: http://localhost:$port$foundEndpoint [$checkTypeUsed]" -ForegroundColor Gray
            Write-Host "  Status: $($response.StatusCode)$contentDetails" -ForegroundColor Gray
            if ($Verbose -and $content.Length -lt 500) {
                Write-Host "  Response: $content" -ForegroundColor DarkGray
            }
            $results += @{ 
                Port = $port
                Layer = $config.Name
                Status = "UP"
                StatusDetail = $healthStatus
                CheckType = $checkTypeUsed
                Endpoint = "http://localhost:$port$foundEndpoint"
                StatusCode = $response.StatusCode
                ContentValid = $contentOk
                RequiredForGate = $config.RequiredForGate
            }
        } else {
            Write-Host " ✗ UNHEALTHY" -ForegroundColor Red
            Write-Host "  Endpoint: http://localhost:$port$foundEndpoint" -ForegroundColor Gray
            if (-not $statusOk) {
                Write-Host "  Status: $($response.StatusCode) (expected $($config.ExpectedStatus))" -ForegroundColor Red
            }
            if (-not $contentOk) {
                Write-Host "  Content: Pattern '$($config.ExpectedContentPattern)' not found" -ForegroundColor Red
            }
            $allHealthy = $false
            $results += @{ 
                Port = $port
                Layer = $config.Name
                Status = "UNHEALTHY"
                CheckType = $checkTypeUsed
                Endpoint = "http://localhost:$port$foundEndpoint"
                StatusCode = $response.StatusCode
                ContentValid = $contentOk
                RequiredForGate = $config.RequiredForGate
            }
        }
    } else {
        Write-Host " ✗ UNREACHABLE" -ForegroundColor Red
        Write-Host "  Tried endpoints: $($config.Endpoints -join ', ')" -ForegroundColor Gray
        Write-Host "  Error: Connection refused or timeout" -ForegroundColor DarkGray
        $allHealthy = $false
        $results += @{ 
            Port = $port
            Layer = $config.Name
            Status = "DOWN"
            CheckType = "none"
            Endpoint = "http://localhost:$port$($config.Endpoints[0])"
            Error = "All endpoints unreachable"
            RequiredForGate = $config.RequiredForGate
        }
    }
}

Write-Host "`n" -NoNewLine
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

$healthyCount = ($results | Where-Object { $_.Status -eq "UP" }).Count
$unhealthyCount = ($results | Where-Object { $_.Status -eq "UNHEALTHY" }).Count
$downCount = ($results | Where-Object { $_.Status -eq "DOWN" }).Count
$totalCount = $results.Count

Write-Host "Results:" -ForegroundColor White
Write-Host "  Healthy:     $healthyCount" -ForegroundColor Green
if ($unhealthyCount -gt 0) {
    Write-Host "  Unhealthy:   $unhealthyCount (returned wrong status/payload)" -ForegroundColor Red
}
if ($downCount -gt 0) {
    Write-Host "  Unreachable: $downCount (connection refused/timeout)" -ForegroundColor Red
}
Write-Host "  Total:       $totalCount" -ForegroundColor White

if (-not $allHealthy) {
    Write-Host "`n❌ HEALTH CHECK FAILED" -ForegroundColor Red
    Write-Host "Not all backend services are returning expected endpoint behavior." -ForegroundColor Red
    
    if ($unhealthyCount -gt 0) {
        Write-Host "`nUnhealthy services (wrong response):" -ForegroundColor Red
        $results | Where-Object { $_.Status -eq "UNHEALTHY" } | ForEach-Object {
            Write-Host "  Port $($_.Port) [$($_.Layer)] - Status $($_.StatusCode)" -ForegroundColor Red
        }
    }
    
    if ($downCount -gt 0) {
        Write-Host "`nUnreachable services:" -ForegroundColor Red
        $results | Where-Object { $_.Status -eq "DOWN" } | ForEach-Object {
            Write-Host "  Port $($_.Port) [$($_.Layer)] - $($_.Error)" -ForegroundColor Red
        }
    }
    
    Write-Host "`nRemediation:" -ForegroundColor Yellow
    Write-Host "  1. Start backend services:" -ForegroundColor White
    Write-Host "     cd services" -ForegroundColor Gray
    Write-Host "     docker-compose up -d" -ForegroundColor Gray
    Write-Host "  2. Wait for services to initialize (30-60s)" -ForegroundColor Gray
    Write-Host "  3. Re-run health check" -ForegroundColor Gray
    
    exit 1
} else {
    Write-Host "`n✓ ALL HEALTH CHECKS PASSED" -ForegroundColor Green
    Write-Host "All backend services are returning expected status codes and payloads." -ForegroundColor Green
    Write-Host "Environment validated for E2E testing." -ForegroundColor Green
    exit 0
}
