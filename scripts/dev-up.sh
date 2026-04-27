#!/usr/bin/env bash
# =============================================================================
# Value Fabric — Local Dev Environment Launcher
# =============================================================================
# Usage:
#   ./scripts/dev-up.sh          # Start everything
#   ./scripts/dev-up.sh --build  # Rebuild containers first
#   ./scripts/dev-up.sh down     # Tear down
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.dev.yml"
ENV_FILE="$PROJECT_ROOT/.env.dev"

cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║           Value Fabric — Local Dev Environment          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Handle 'down' command
if [[ "${1:-}" == "down" ]]; then
    echo -e "${YELLOW}Tearing down dev environment...${NC}"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down -v
    echo -e "${GREEN}Done.${NC}"
    exit 0
fi

banner

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &>/dev/null; then
    echo -e "${RED}Error: docker is not installed.${NC}"
    exit 1
fi

if ! docker compose version &>/dev/null; then
    echo -e "${RED}Error: docker compose plugin is not installed.${NC}"
    echo "Install with: sudo apt install docker-compose-plugin"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Compose available${NC}"

# Check for .env.dev
if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${RED}Error: .env.dev not found. Copy from template:${NC}"
    echo "  cp .env.dev.example .env.dev"
    exit 1
fi

echo -e "${GREEN}✓ .env.dev found${NC}"

# Optional: check for LLM keys
if grep -q "^OPENAI_API_KEY=$" "$ENV_FILE" 2>/dev/null; then
    echo -e "${YELLOW}⚠ OPENAI_API_KEY not set — ValuePilot will use heuristic mode${NC}"
    echo -e "  Set it in .env.dev for full LLM responses."
fi

# Build and start
echo ""
echo -e "${YELLOW}Starting services...${NC}"

BUILD_FLAG=""
if [[ "${1:-}" == "--build" ]]; then
    BUILD_FLAG="--build"
fi

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d $BUILD_FLAG

# Wait for health
echo ""
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"

MAX_WAIT=120
ELAPSED=0
while [[ $ELAPSED -lt $MAX_WAIT ]]; do
    HEALTHY=$(docker compose -f "$COMPOSE_FILE" ps --format json 2>/dev/null | python3 -c "
import sys, json
lines = sys.stdin.read().strip().split('\n')
total = 0
healthy = 0
for line in lines:
    if not line: continue
    try:
        svc = json.loads(line)
        total += 1
        status = svc.get('Health', svc.get('State', ''))
        if 'healthy' in status.lower() or 'running' in status.lower():
            healthy += 1
    except: pass
print(f'{healthy}/{total}')
" 2>/dev/null || echo "0/0")

    echo -ne "\r  Services healthy: ${HEALTHY}  (${ELAPSED}s elapsed)"

    if [[ "$HEALTHY" == *"/"* ]]; then
        CURRENT=$(echo "$HEALTHY" | cut -d/ -f1)
        TOTAL=$(echo "$HEALTHY" | cut -d/ -f2)
        if [[ "$CURRENT" -ge "$TOTAL" && "$TOTAL" -gt 0 ]]; then
            echo ""
            break
        fi
    fi

    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Dev environment is ready!${NC}"
echo ""
echo -e "  ${CYAN}Frontend:${NC}  http://localhost:3001"
echo -e "  ${CYAN}Layer 4 API:${NC}  http://localhost:8004"
echo -e "  ${CYAN}Neo4j Browser:${NC}  http://localhost:7474"
echo -e "  ${CYAN}PostgreSQL:${NC}  localhost:5432 (postgres/postgres)"
echo -e "  ${CYAN}Redis:${NC}  localhost:6379"
echo ""
echo -e "  ${YELLOW}Auth:${NC} Bypassed — all requests auto-authenticated"
echo -e "  ${YELLOW}Tenant:${NC} 00000000-0000-4000-a000-000000000001"
echo ""
echo -e "  To stop:  ${CYAN}./scripts/dev-up.sh down${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
