#!/bin/bash
# Task 46 - Monitoring Readiness Validation Script
# Run this after docker-compose up to validate monitoring stack

set -e

echo "=== Task 46 Monitoring Validation ==="
echo ""

# Wait for services to be healthy
echo "Waiting for monitoring services..."
sleep 10

# 1. Prometheus target health
echo ""
echo "[1/5] Prometheus Targets Health"
curl -fsS http://localhost:9090/api/v1/targets 2>/dev/null | jq '.data.activeTargets | map({job: .labels.job, health: .health, lastError: .lastError})' || echo "  ERROR: Cannot reach Prometheus"

# 2. Prometheus rules load status
echo ""
echo "[2/5] Prometheus Rules Load Status"
curl -fsS http://localhost:9090/api/v1/rules 2>/dev/null | jq '.data.groups | map({name: .name, file: .file, rules: .rules | length})' || echo "  ERROR: Cannot load rules"

# 3. Prometheus alerts status
echo ""
echo "[3/5] Prometheus Alerts Status"
curl -fsS http://localhost:9090/api/v1/alerts 2>/dev/null | jq '.data.alerts | length' || echo "  ERROR: Cannot check alerts"
echo "  Active alerts: $(curl -fsS http://localhost:9090/api/v1/alerts 2>/dev/null | jq '.data.alerts | length')"

# 4. Alertmanager status
echo ""
echo "[4/5] Alertmanager Status"
curl -fsS http://localhost:9093/api/v2/status 2>/dev/null | jq '{cluster: .cluster.status, version: .versionInfo.version}' || echo "  ERROR: Cannot reach Alertmanager"

# 5. Alert pipeline smoke test
echo ""
echo "[5/5] Alert Pipeline Smoke Test"
SMOKE_RESULT=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[{"labels":{"alertname":"Task46Smoke","severity":"warning"},"annotations":{"summary":"Task 46 smoke alert"}}]')

if [ "$SMOKE_RESULT" = "200" ]; then
    echo "  SUCCESS: Alertmanager accepted test alert (HTTP 200)"
else
    echo "  ERROR: Alertmanager returned HTTP $SMOKE_RESULT"
fi

echo ""
echo "=== Validation Complete ==="
echo ""
echo "Next steps if any checks failed:"
echo "1. Verify all app services are healthy: docker-compose ps"
echo "2. Check Prometheus logs: docker-compose logs prometheus"
echo "3. Check Alertmanager logs: docker-compose logs alertmanager"
echo "4. Access Prometheus UI: http://localhost:9090/targets"
echo "5. Access Grafana UI: http://localhost:3000 (admin/admin)"
