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
FINALIZED="false"

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
CONTAINER_STATUS_FILE="$ARTIFACT_DIR/container-status.txt"
HEALTH_STATUS_FILE="$ARTIFACT_DIR/container-health.jsonl"
ENDPOINT_PROBES_FILE="$ARTIFACT_DIR/endpoint-probes.tsv"
SERVICE_LOG_DIR="$ARTIFACT_DIR/service-logs"
SEED_REPORT_JSON="$ARTIFACT_DIR/seed-report.json"
PLAYWRIGHT_ARTIFACT_DIR="$ARTIFACT_DIR/playwright"
PLAYWRIGHT_HTML_REPORT="$PLAYWRIGHT_ARTIFACT_DIR/html"
PLAYWRIGHT_JUNIT_FILE="$PLAYWRIGHT_ARTIFACT_DIR/junit.xml"

exec > >(tee "$LOG_FILE") 2>&1

cd "$ROOT_DIR"

services=(postgres redis neo4j minio layer1 layer2 layer3 layer4 layer5 layer6 frontend)

section() {
  printf '\n## %s\n' "$1"
}

sanitize_stream() {
  sed -E \
    -e 's#(postgresql|postgres|mysql|redis|mongodb)://[^[:space:]@]+:[^[:space:]@]+@#\1://[REDACTED]@#Ig' \
    -e 's#(Authorization: )[^
[:space:]]+#\1[REDACTED]#Ig' \
    -e 's#((password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)[[:space:]_:-]*=)[^[:space:],;]+#\1[REDACTED]#Ig'
}

write_summary() {
  local status="$1"
  local detail="$2"
  FINALIZED="true"
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
| compose_config | ${COMPOSE_CONFIG_FILE} |
| container_status | ${CONTAINER_STATUS_FILE} |
| health_status | ${HEALTH_STATUS_FILE} |
| endpoint_probes | ${ENDPOINT_PROBES_FILE} |
| service_logs | ${SERVICE_LOG_DIR} |
| seed_report_json | ${SEED_REPORT_JSON} |
| playwright_artifacts | ${PLAYWRIGHT_ARTIFACT_DIR} |

SUMMARY
}

compose_ps_safe() {
  docker-compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" ps 2>&1 | sanitize_stream || true
}

probe_endpoint() {
  local name="$1"
  local url="$2"
  local output_file="$3"
  local code
  code="$(curl -k -L -sS -o "$output_file" -w '%{http_code}' --max-time 15 "$url" 2>>"$ARTIFACT_DIR/curl-errors.log" || true)"
  if [[ -z "$code" ]]; then
    code="000"
  fi
  printf '%s\t%s\t%s\n' "$name" "$url" "$code" >> "$ENDPOINT_PROBES_FILE"
  [[ "$code" =~ ^2|3[0-9][0-9]$ ]]
}

collect_evidence() {
  local reason="$1"
  section "evidence collection: $reason"
  mkdir -p "$SERVICE_LOG_DIR"
  {
    echo "# Container Status"
    echo "reason=$reason"
    compose_ps_safe
  } > "$CONTAINER_STATUS_FILE"

  : > "$HEALTH_STATUS_FILE"
  for service in "${services[@]}"; do
    local cid state
    cid="$(docker-compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null || true)"
    if [[ -z "$cid" ]]; then
      printf '{"service":"%s","container_id":"","state":"missing"}\n' "$service" >> "$HEALTH_STATUS_FILE"
      continue
    fi
    state="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid" 2>/dev/null || echo inspect-failed)"
    printf '{"service":"%s","container_id":"%s","state":"%s"}\n' "$service" "$cid" "$state" >> "$HEALTH_STATUS_FILE"
    docker logs --tail 160 "$cid" 2>&1 | sanitize_stream > "$SERVICE_LOG_DIR/${service}.log" || true
  done

  : > "$ENDPOINT_PROBES_FILE"
  printf 'name\turl\tstatus_code\n' > "$ENDPOINT_PROBES_FILE"
  probe_endpoint frontend "$FRONTEND_URL" "$ARTIFACT_DIR/frontend-probe.html" || true
  probe_endpoint backend_health "$BACKEND_URL/health" "$ARTIFACT_DIR/backend-health.json" || true

  echo "evidence artifacts written under $ARTIFACT_DIR"
}

fail() {
  local status="$1"
  local detail="$2"
  echo "ERROR: $detail" >&2
  if [[ "$CONFIG_ONLY" != "true" ]]; then
    collect_evidence "$detail"
  fi
  write_summary "$status" "$detail"
  exit 1
}

on_unhandled_error() {
  local exit_code="$?"
  local line_no="$1"
  if [[ "$FINALIZED" != "true" ]]; then
    if [[ "$CONFIG_ONLY" != "true" ]]; then
      collect_evidence "unhandled error at line $line_no"
    fi
    write_summary "FAIL" "unhandled error at line $line_no; exit code $exit_code"
  fi
  exit "$exit_code"
}
trap 'on_unhandled_error $LINENO' ERR

if [[ "${VITE_USE_MOCKS:-false}" =~ ^(1|true|yes|on)$ ]] || [[ "${VITE_ENABLE_MOCK_FALLBACK:-false}" =~ ^(1|true|yes|on)$ ]]; then
  fail "FAIL" "mock flags must not be enabled for live workflow validation"
fi

section "tooling"
command -v docker-compose >/dev/null || fail "BLOCKED" "docker-compose is required in this validation environment"
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
  compose_ps_safe || true
  fail "BLOCKED" "timed out waiting for live stack health"
fi

section "endpoint probes"
: > "$ENDPOINT_PROBES_FILE"
printf 'name\turl\tstatus_code\n' > "$ENDPOINT_PROBES_FILE"
probe_endpoint frontend "$FRONTEND_URL" "$ARTIFACT_DIR/frontend-probe.html" || fail "FAIL" "frontend probe failed at $FRONTEND_URL"
probe_endpoint backend_health "$BACKEND_URL/health" "$ARTIFACT_DIR/backend-health.json" || fail "FAIL" "backend health probe failed at $BACKEND_URL/health"
cat "$ENDPOINT_PROBES_FILE"

if [[ "$RUN_LIVE_SEED" == "true" ]]; then
  section "live seed"
  docker-compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" --profile seed run --rm \
    -e SEED_REPORT_JSON=/artifacts/seed-report.json \
    -e SEED_STRICT=true \
    -v "$ARTIFACT_DIR:/artifacts" \
    live-seed
fi

if [[ "$RUN_LIVE_PLAYWRIGHT" == "true" ]]; then
  section "live playwright p0"
  mkdir -p "$PLAYWRIGHT_ARTIFACT_DIR"
  (
    cd apps/web
    PLAYWRIGHT_LIVE_MODE=true \
    PLAYWRIGHT_LIVE_FRONTEND_URL="$FRONTEND_URL" \
    PLAYWRIGHT_BACKEND_URL="$BACKEND_URL" \
    PLAYWRIGHT_HTML_REPORT="$PLAYWRIGHT_HTML_REPORT" \
    PLAYWRIGHT_JUNIT_FILE="$PLAYWRIGHT_JUNIT_FILE" \
    PLAYWRIGHT_OUTPUT_DIR="$PLAYWRIGHT_ARTIFACT_DIR/test-results" \
    VITE_USE_MOCKS=false \
    VITE_ENABLE_MOCK_FALLBACK=false \
    pnpm run test:e2e:live:p0
  )

  [[ -f "$PLAYWRIGHT_HTML_REPORT/index.html" ]] || fail "FAIL" "Playwright HTML report is missing at $PLAYWRIGHT_HTML_REPORT/index.html"
  [[ -f "$PLAYWRIGHT_JUNIT_FILE" ]] || fail "FAIL" "Playwright JUnit report is missing at $PLAYWRIGHT_JUNIT_FILE"
  if ! find "$PLAYWRIGHT_ARTIFACT_DIR/test-results" -type f -name '*.zip' -print -quit 2>/dev/null | grep -q .; then
    fail "FAIL" "Playwright live trace artifact is missing under $PLAYWRIGHT_ARTIFACT_DIR/test-results"
  fi
fi

collect_evidence "successful validation"
write_summary "PASS" "live stack health probes passed; seed/playwright statuses reflect requested options"
section "summary"
cat "$SUMMARY_FILE"
