#!/usr/bin/env bash
# dev-preflight.sh — Pre-flight checks before starting services
#
# Validates that Docker daemon is running, required env files exist,
# and essential ports are available before attempting docker compose up.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0

echo "🔍 Running pre-flight checks..."
echo ""

# 0. Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ -n "$python_version" ]]; then
    major=$(echo "$python_version" | cut -d'.' -f1)
    minor=$(echo "$python_version" | cut -d'.' -f2)
    if [[ "$major" -eq 3 && "$minor" -ge 11 ]]; then
        echo -e "${GREEN}✓${NC} Python 3.11+ found ($python_version)"
    else
        echo -e "${RED}✗${NC} Python 3.11+ required (found: $python_version)"
        echo "  → Install Python 3.11: https://www.python.org/downloads/"
        errors=$((errors + 1))
    fi
else
    echo -e "${RED}✗${NC} Python 3 not found"
    echo "  → Install Python 3.11: https://www.python.org/downloads/"
    errors=$((errors + 1))
fi

# 0b. Node.js version
echo "Checking Node.js version..."
node_version=$(node --version 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1)
if [[ -n "$node_version" ]]; then
    if [[ "$node_version" -ge 20 ]]; then
        echo -e "${GREEN}✓${NC} Node.js 20+ found (v$(node --version | cut -d'v' -f2))"
    else
        echo -e "${RED}✗${NC} Node.js 20+ required (found: v$(node --version | cut -d'v' -f2))"
        echo "  → Install Node.js 20: https://nodejs.org/"
        errors=$((errors + 1))
    fi
else
    echo -e "${RED}✗${NC} Node.js not found"
    echo "  → Install Node.js 20: https://nodejs.org/"
    errors=$((errors + 1))
fi

echo ""

# 1. Docker daemon
echo "Checking Docker daemon..."
if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker daemon is running"
else
    echo -e "${RED}✗${NC} Docker daemon is not running"
    echo "  → Start Docker Desktop or run: sudo systemctl start docker"
    errors=$((errors + 1))
fi

# 2. Docker Compose
echo "Checking Docker Compose..."
if docker compose version >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker Compose is available"
else
    echo -e "${RED}✗${NC} Docker Compose is not available"
    echo "  → Install Docker Compose: https://docs.docker.com/compose/install/"
    errors=$((errors + 1))
fi

# 3. .env file
echo "Checking .env file..."
FABRIC_DIR="$(cd "$(dirname "$0")/../value-fabric" && pwd)"
if [ -f "$FABRIC_DIR/.env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
else
    echo -e "${YELLOW}!${NC} .env file missing — generating from .env.example"
    if [ -f "$FABRIC_DIR/.env.example" ]; then
        cp "$FABRIC_DIR/.env.example" "$FABRIC_DIR/.env"
        echo -e "  → Created $FABRIC_DIR/.env (review and update secrets before production use)"
    else
        echo -e "${RED}✗${NC} .env.example not found at $FABRIC_DIR/.env.example"
        errors=$((errors + 1))
    fi
fi

# 4. Required ports
echo ""
echo "Checking required ports..."

check_port() {
    local port=$1
    local service=$2
    if command -v ss >/dev/null 2>&1; then
        if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
            echo -e "${YELLOW}!${NC} Port $port ($service) is already in use"
        else
            echo -e "${GREEN}✓${NC} Port $port ($service) is available"
        fi
    elif command -v lsof >/dev/null 2>&1; then
        if lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
            echo -e "${YELLOW}!${NC} Port $port ($service) is already in use"
        else
            echo -e "${GREEN}✓${NC} Port $port ($service) is available"
        fi
    fi
}

check_port 5432 "PostgreSQL"
check_port 6379 "Redis"
check_port 7474 "Neo4j Browser"
check_port 7687 "Neo4j Bolt"
check_port 8000 "Layer 2 API"
check_port 8001 "Layer 3 API"
check_port 8002 "Layer 4 API"

echo ""
if [ "$errors" -gt 0 ]; then
    echo -e "${RED}Pre-flight failed with $errors error(s). Fix the issues above before starting services.${NC}"
    exit 1
else
    echo -e "${GREEN}All pre-flight checks passed. Ready to start services.${NC}"
fi
