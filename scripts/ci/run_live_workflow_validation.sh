#!/usr/bin/env bash
# Fail-closed live workflow validation runner for Fabric_4L.
#
# This script is intentionally conservative: it always validates compose syntax
# and service health, and it runs seed/Playwright only when explicitly enabled.
# It writes sanitized evidence artifacts under artifacts/live-workflow-validation.

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.live.yml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-fabric4l_live_validation}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$ROOT_DIR/artifacts/live-workflow-validation}"
FRONTEND_URL="${PLAYWRIGHT_LIVE_FRONTEND_URL:-http://localhost:3001}"
BACKEND_URL="${PLAYWRIGHT_BACKEND_URL:-http://localhost:8004}"
HEALTH_TIMEOUT_SECONDS="${HEALTH_TIMEOUT_SECONDS:-360}"
RUN_LIVE_SEED="${RUN_LIVE_SEED:-false}"
RUN_LIVE_PLAYWRIGHT="${RUN_LIVE_PLAYWRIGHT:-false}"
CONFIG_ONLY="false"
START_STACK="true"

usage() {
  cat <<'USAGE'
Usage: scripts/ci/run_live_workflow_validation.sh [options]

Options:
  --config-only       Validate docker-compose.live.yml and frontend guardrails only.
  --no-start          Do not start or rebuild containers; probe the currently running stack.
  --seed              Run the guarded live seed step after services become healthy.
  --playwright        Run the guarded live Playwright P0 suite after services become healthy.
  --help              Show this help text.

Environment overrides:
  COMPOSE_FILE=docker-compose.live.yml
  COMPOSE_PROJECT_NAME=fabric4l_live_validation
  ARTIFACT_DIR=artifacts/live-workflow-validation
  PLAYWRIGHT_LIVE_FRONTEND_URL=http://localhost:3001
  PLAYWRIGHT_BACKEND_URL=http://localhost:8004
  HEALTH_TIMEOUT_SECONDS=360
  RUN_LIVE_SEED=true|false
  RUN_LIVE_PLAYWRIGHT=true|false
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config-only)
      CONFIG_ONLY="true"
      START_STACK="false"
      ;;
    --no-start)
      START_STACK="false"
      ;;
    --seed)
      RUN_LIVE_SEED="true"
      ;;
    --playwright)
      RUN_LIVE_PLAYWRIGHT="true"
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

mkdir -p "$ARTIFACT_DIR"
LOG_FILE="$ARTIFACT_DIR/live-workflow-validation.log"
SUMMARY_FILE="$ARTIFACT_DIR/live-workflow-validation-summary.md"
COMPOSE_CONFIG_FILE="$ARTIFACT_DIR/docker-compose.live.resolved.yml"

exec > >(tee "$LOG_FILE") 2>&1

cd "$ROOT_DIR"

section() {
  printf '\n## %s\n' "$1"
}

fail() {
  echo "ERROR: $*" >&2
  write_summary "FAIL" "$*"
  exit 1
}

write_summary() {
  local status="$1"
  local detail="$2"
  cat > "$SUMMARY_FILE" <<SUMMARY
# Live Workflow Validation Summary

| Field | Value |
| --- | --- |
| status | ${status} |
| detail | ${detail} |
| compose_file | ${COMPOSE_FILE} |
| frontend_url | ${FRONTEND_URL} |
| backend_url | ${BACKEND_URL} |
| seed_requested | ${RUN_LIVE_SEED} |
| playwright_requested | ${RUN_LIVE_PLAYWRIGHT} |
| log_file | ${LOG_FILE} |

SUMMARY
}

if [[ "${VITE_USE_MOCKS:-false}" =~ ^(1|true|yes|on)$ ]] || [[ "${VITE_ENABLE_MOCK_FALLBACK:-false}" =~ ^(1|true|yes|on)$ ]]; then
  fail "mock flags must not be enabled for live workflow validation"
fi

section "tooling"
command -v docker-compose >/dev/null || fail "docker-compose is required in this validation environment"
docker-compose --version
node --version
pnpm --version || true

section "frontend guardrails"
(
  cd apps/web
  PLAYWRIGHT_LIVE_MODE=true \
  PLAYWRIGHT_LIVE_FRONTEND_URL="$FRONTEND_URL" \
  PLAYWRIGHT_BACKEND_URL="$BACKEND_URL" \
  VITE_USE_MOCKS=false \
  VITE_ENABLE_MOCK_FALLBACK=false \
  node scripts/live-env-guard.mjs test
)

section "compose config"
docker-compose -f "$COMPOSE_FILE" config > "$COMPOSE_CONFIG_FILE"
echo "resolved compose saved to $COMPOSE_CONFIG_FILE"

if [[ "$CONFIG_ONLY" == "true" ]]; then
  write_summary "PASS" "compose config and frontend live guardrails passed"
  echo "config-only validation completed"
  exit 0
fi

if [[ "$START_STACK" == "true" ]]; then
  section "stack startup"
  docker-compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" up -d --build
else
  section "stack startup skipped"
  echo "probing currently running containers"
fi

section "health wait"
deadline=$((SECONDS + HEALTH_TIMEOUT_SECONDS))
services=(postgres redis neo4j minio layer1 layer2 layer3 layer4 layer5 layer6 frontend)
while (( SECONDS < deadline )); do
  unhealthy=()
  for service in "${services[@]}"; do
    cid="$(docker-compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null || true)"
    if [[ -z "$cid" ]]; then
      unhealthy+=("$service:missing")
      continue
    fi
    state="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid" 2>/dev/null || echo inspect-failed)"
    if [[ "$state" != "healthy" && "$state" != "running" ]]; then
      unhealthy+=("$service:$state")
    fi
  done
  if [[ ${#unhealthy[@]} -eq 0 ]]; then
    echo "all required services are healthy/running"
    break
  fi
  echo "waiting for services: ${unhealthy[*]}"
  sleep 10
done

if (( SECONDS >= deadline )); then
  section "container status"
  docker-compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" ps || true
  fail "timed out waiting for live stack health"
fi

section "endpoint probes"
curl -fsS "$FRONTEND_URL" >/tmp/fabric4l_live_frontend_probe.html || fail "frontend probe failed at $FRONTEND_URL"
curl -fsS "$BACKEND_URL/health" || fail "backend health probe failed at $BACKEND_URL/health"

if [[ "$RUN_LIVE_SEED" == "true" ]]; then
  section "live seed"
  docker-compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" --profile seed run --rm live-seed
fi

if [[ "$RUN_LIVE_PLAYWRIGHT" == "true" ]]; then
  section "live playwright p0"
  (
    cd apps/web
    PLAYWRIGHT_LIVE_MODE=true \
    PLAYWRIGHT_LIVE_FRONTEND_URL="$FRONTEND_URL" \
    PLAYWRIGHT_BACKEND_URL="$BACKEND_URL" \
    VITE_USE_MOCKS=false \
    VITE_ENABLE_MOCK_FALLBACK=false \
    pnpm run test:e2e:live:p0
  )
fi

write_summary "PASS" "live stack health probes passed; seed/playwright statuses reflect requested options"
section "summary"
cat "$SUMMARY_FILE"
