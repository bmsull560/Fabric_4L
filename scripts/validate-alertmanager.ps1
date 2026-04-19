#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Validates Alertmanager deployment in a Kubernetes cluster.

.DESCRIPTION
    This script performs comprehensive validation of the Alertmanager deployment,
    including manifest validation, secret verification, network policy checks,
    and a test alert flow to verify notifications reach Slack/PagerDuty.

.PARAMETER Namespace
    The Kubernetes namespace where Alertmanager is deployed (default: value-fabric)

.PARAMETER TestAlert
    If set, sends a test alert to verify end-to-end notification flow

.EXAMPLE
    ./validate-alertmanager.ps1 -Namespace value-fabric -TestAlert

.NOTES
    Requires kubectl configured with cluster access.
    File: validate-alertmanager.ps1
#>
param(
    [string]$Namespace = "value-fabric",
    [switch]$TestAlert
)

$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Alertmanager Deployment Validation" -ForegroundColor Cyan
Write-Host "Namespace: $Namespace" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

$validationResults = @{
    Manifests = $false
    ConfigMap = $false
    Deployment = $false
    Service = $false
    PVC = $false
    Secrets = $false
    NetworkPolicy = $false
    PrometheusConfig = $false
}

# 1. Validate Kustomize Build
Write-Host "[1/8] Validating Kustomize manifests..." -ForegroundColor Yellow
try {
    $kustomizeOutput = kubectl kustomize k8s/overlays/dev 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Kustomize build successful" -ForegroundColor Green
        $validationResults.Manifests = $true
    } else {
        Write-Host "  ✗ Kustomize build failed: $kustomizeOutput" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Kustomize error: $_" -ForegroundColor Red
}

# 2. Check ConfigMap
Write-Host "[2/8] Checking Alertmanager ConfigMap..." -ForegroundColor Yellow
try {
    $configmap = kubectl get configmap alertmanager-config -n $Namespace -o json 2>&1 | ConvertFrom-Json
    if ($configmap.data.'alertmanager.yml') {
        Write-Host "  ✓ ConfigMap alertmanager-config exists with alertmanager.yml" -ForegroundColor Green
        $validationResults.ConfigMap = $true
    } else {
        Write-Host "  ✗ ConfigMap missing alertmanager.yml key" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ ConfigMap not found: $_" -ForegroundColor Red
}

# 3. Check Deployment
Write-Host "[3/8] Checking Alertmanager Deployment..." -ForegroundColor Yellow
try {
    $deployment = kubectl get deployment alertmanager -n $Namespace -o json 2>&1 | ConvertFrom-Json
    $readyReplicas = $deployment.status.readyReplicas
    $desiredReplicas = $deployment.spec.replicas
    
    if ($readyReplicas -ge 1) {
        Write-Host "  ✓ Deployment ready: $readyReplicas/$desiredReplicas replicas" -ForegroundColor Green
        $validationResults.Deployment = $true
    } else {
        Write-Host "  ✗ Deployment not ready: $readyReplicas/$desiredReplicas replicas" -ForegroundColor Red
        Write-Host "        Check: kubectl describe deployment alertmanager -n $Namespace" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ Deployment not found: $_" -ForegroundColor Red
}

# 4. Check Service
Write-Host "[4/8] Checking Alertmanager Service..." -ForegroundColor Yellow
try {
    $service = kubectl get service alertmanager -n $Namespace -o json 2>&1 | ConvertFrom-Json
    $selector = $service.spec.selector.app
    if ($selector -eq "alertmanager") {
        Write-Host "  ✓ Service alertmanager exists with correct selector" -ForegroundColor Green
        $validationResults.Service = $true
    } else {
        Write-Host "  ✗ Service selector mismatch: $selector" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Service not found: $_" -ForegroundColor Red
}

# 5. Check PVC
Write-Host "[5/8] Checking Alertmanager PVC..." -ForegroundColor Yellow
try {
    $pvc = kubectl get pvc alertmanager-data -n $Namespace -o json 2>&1 | ConvertFrom-Json
    $phase = $pvc.status.phase
    if ($phase -eq "Bound") {
        Write-Host "  ✓ PVC alertmanager-data is Bound" -ForegroundColor Green
        $validationResults.PVC = $true
    } else {
        Write-Host "  ✗ PVC status: $phase" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ PVC not found: $_" -ForegroundColor Red
}

# 6. Check Secrets
Write-Host "[6/8] Checking Alertmanager Secrets..." -ForegroundColor Yellow
try {
    $secret = kubectl get secret alertmanager-secrets -n $Namespace -o json 2>&1 | ConvertFrom-Json
    $keys = $secret.data.PSObject.Properties.Name
    $requiredKeys = @('slack_webhook_url', 'pagerduty_integration_key')
    $missingKeys = $requiredKeys | Where-Object { $_ -notin $keys }
    
    if ($missingKeys.Count -eq 0) {
        Write-Host "  ✓ Secret alertmanager-secrets exists with required keys" -ForegroundColor Green
        $validationResults.Secrets = $true
    } else {
        Write-Host "  ✗ Secret missing keys: $($missingKeys -join ', ')" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Secret not found: $_" -ForegroundColor Red
}

# 7. Check Network Policies
Write-Host "[7/8] Checking Network Policies..." -ForegroundColor Yellow
try {
    $npEgress = kubectl get networkpolicy alertmanager-egress -n $Namespace 2>&1
    $npIngress = kubectl get networkpolicy alertmanager-ingress -n $Namespace 2>&1
    
    if ($npEgress -match "alertmanager-egress" -and $npIngress -match "alertmanager-ingress") {
        Write-Host "  ✓ Network policies alertmanager-egress and alertmanager-ingress exist" -ForegroundColor Green
        $validationResults.NetworkPolicy = $true
    } else {
        Write-Host "  ✗ Network policies missing" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Network policies not found: $_" -ForegroundColor Red
}

# 8. Check Prometheus Configuration
Write-Host "[8/8] Checking Prometheus alertmanager configuration..." -ForegroundColor Yellow
try {
    $promConfig = kubectl get configmap prometheus-config -n $Namespace -o jsonpath='{.data.prometheus\.yml}' 2>&1
    if ($promConfig -match "alertmanager:9093" -and $promConfig -match 'job_name: "alertmanager"') {
        Write-Host "  ✓ Prometheus configured with alertmanager target" -ForegroundColor Green
        $validationResults.PrometheusConfig = $true
    } else {
        Write-Host "  ✗ Prometheus missing alertmanager configuration" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Prometheus config not accessible: $_" -ForegroundColor Red
}

# Summary
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

$passed = ($validationResults.Values | Where-Object { $_ -eq $true }).Count
$total = $validationResults.Count

foreach ($check in $validationResults.GetEnumerator() | Sort-Object Name) {
    $status = if ($check.Value) { "✓ PASS" } else { "✗ FAIL" }
    $color = if ($check.Value) { "Green" } else { "Red" }
    Write-Host "$status - $($check.Name)" -ForegroundColor $color
}

Write-Host ""
Write-Host "Result: $passed/$total checks passed" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Yellow" })

# Optional: Test Alert Flow
if ($TestAlert) {
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host "Test Alert Flow" -ForegroundColor Cyan
    Write-Host "======================================" -ForegroundColor Cyan
    
    Write-Host "Sending test alert via Prometheus API..." -ForegroundColor Yellow
    Write-Host "Note: This requires Prometheus to be running with admin API enabled" -ForegroundColor Gray
    
    # Port-forward Prometheus for testing
    Write-Host "Port-forwarding Prometheus to localhost:9090..." -ForegroundColor Gray
    $pfJob = Start-Job { kubectl port-forward svc/prometheus 9090:9090 -n $using:Namespace }
    Start-Sleep -Seconds 3
    
    try {
        # Trigger test alert
        $alertPayload = @{
            labels = @{
                alertname = "TestAlert"
                severity = "warning"
                namespace = $Namespace
            }
            annotations = @{
                summary = "Test alert from validation script"
                description = "This is a test alert to validate Alertmanager notification flow"
                runbook_url = "https://github.com/bmsull560/Fabric_4L/tree/main/docs/runbooks"
            }
            generatorURL = "http://prometheus:9090/graph"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/alerts" -Method Post -Body "[$alertPayload]" -ContentType "application/json" -ErrorAction SilentlyContinue
        
        if ($response.status -eq "success") {
            Write-Host "  ✓ Test alert sent successfully" -ForegroundColor Green
            Write-Host "        Check your Slack channel #vf-alerts-warning for the test notification" -ForegroundColor Gray
            Write-Host "        Alert should arrive within 30-60 seconds" -ForegroundColor Gray
        } else {
            Write-Host "  ✗ Failed to send test alert: $($response.error)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ✗ Test alert failed: $_" -ForegroundColor Red
        Write-Host "        Note: Prometheus admin API may not be enabled or port-forward failed" -ForegroundColor Gray
    } finally {
        Stop-Job $pfJob -ErrorAction SilentlyContinue
        Remove-Job $pfJob -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "Validation complete!" -ForegroundColor Cyan

if ($passed -ne $total) {
    exit 1
}
