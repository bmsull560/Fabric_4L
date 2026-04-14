#!/usr/bin/env bash
set -euo pipefail

# Post-deploy smoke tests for k8s ephemeral deployments
# Waits for rollout status and performs HTTP health checks

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${NAMESPACE:-default}"
TIMEOUT="${TIMEOUT:-300s}"
FAILURES=0

echo "=== K8s Post-Deploy Smoke Tests ==="
echo "Namespace: ${NAMESPACE}"
echo "Timeout: ${TIMEOUT}"
echo ""

# Helper to check if a deployment exists and wait for rollout
check_rollout() {
    local name="$1"
    if kubectl get deployment "${name}" -n "${NAMESPACE}" &>/dev/null; then
        echo "Waiting for rollout of ${name}..."
        if kubectl rollout status deployment/${name} -n ${NAMESPACE} --timeout=${TIMEOUT}; then
            echo "✅ ${name} rolled out successfully"
            return 0
        else
            echo "❌ ${name} rollout failed or timed out"
            return 1
        fi
    else
        echo "⚠️ Deployment ${name} not found, skipping"
        return 0
    fi
}

# Check all expected deployments
echo "Checking deployment rollouts..."
check_rollout "layer1-ingestion" || ((FAILURES++))
check_rollout "layer2-extraction" || ((FAILURES++))
check_rollout "layer3-knowledge" || ((FAILURES++))
check_rollout "layer4-agents" || ((FAILURES++))
check_rollout "layer5-ground-truth" || ((FAILURES++))
check_rollout "frontend" || ((FAILURES++))

echo ""
echo "=== HTTP Health Checks ==="

# Port-forward helper for health checks
# In ephemeral clusters, we use service cluster IPs or port-forward
check_health() {
    local service="$1"
    local port="$2"
    local path="${3:-/health}"
    local max_attempts=30
    local attempt=1

    echo "Checking health of ${service}:${port}${path}..."

    # Use kubectl port-forward in background
    local local_port=$((port + 10000))
    kubectl port-forward svc/${service} ${local_port}:${port} -n ${NAMESPACE} &>/tmp/portforward-${service}.log &
    local pf_pid=$!

    # Wait for port-forward to establish
    sleep 2

    # Try health check
    while [ $attempt -le $max_attempts ]; do
        if curl -sf http://localhost:${local_port}${path} &>/dev/null; then
            echo "✅ ${service} health check passed"
            kill $pf_pid 2>/dev/null || true
            return 0
        fi
        sleep 2
        ((attempt++))
    done

    echo "❌ ${service} health check failed after ${max_attempts} attempts"
    kill $pf_pid 2>/dev/null || true
    return 1
}

# Run health checks (with port-forward)
check_health "layer1-ingestion" 8000 "/api/v1/ingestion/health" || ((FAILURES++))
check_health "layer2-extraction" 8000 "/api/v1/extraction/health" || ((FAILURES++))
check_health "layer3-knowledge" 8000 "/api/v1/knowledge/health" || ((FAILURES++))
check_health "layer4-agents" 8000 "/api/v1/agents/health" || ((FAILURES++))
check_health "layer5-ground-truth" 8000 "/api/v1/ground-truth/health" || ((FAILURES++))
check_health "frontend" 80 "/" || ((FAILURES++))

echo ""
echo "=== Smoke Test Summary ==="
if [ $FAILURES -eq 0 ]; then
    echo "✅ All smoke tests passed"
    exit 0
else
    echo "❌ ${FAILURES} smoke test(s) failed"
    exit 1
fi
