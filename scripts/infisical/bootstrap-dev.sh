#!/usr/bin/env bash
# bootstrap-dev.sh — Local developer onboarding for Infisical-managed secrets.
#
# Prerequisites:
#   1. Install the Infisical CLI: https://infisical.com/docs/cli/overview
#   2. Have access to the fabric-4l Infisical project
#
# Usage:
#   ./scripts/infisical/bootstrap-dev.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔐 Value Fabric — Infisical Bootstrap (Dev)"
echo "============================================="
echo ""

# ── Step 1: Check Infisical CLI ──────────────────────────────────────────────
if ! command -v infisical &> /dev/null; then
  echo -e "${RED}✗ Infisical CLI not found.${NC}"
  echo "  Install it from: https://infisical.com/docs/cli/overview"
  echo ""
  echo "  macOS:   brew install infisical/get-cli/infisical"
  echo "  Linux:   curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | sudo -E bash && sudo apt-get install infisical"
  echo "  Windows: scoop bucket add org https://github.com/nicholasgasior/scoop-bucket && scoop install infisical"
  exit 1
fi
echo -e "${GREEN}✓ Infisical CLI found:${NC} $(infisical --version 2>/dev/null || echo 'version unknown')"

# ── Step 2: Check login ─────────────────────────────────────────────────────
echo ""
echo "Checking Infisical authentication..."
if ! infisical user 2>/dev/null | grep -q "email"; then
  echo -e "${YELLOW}⚠ Not logged in. Running 'infisical login'...${NC}"
  infisical login
fi
echo -e "${GREEN}✓ Authenticated with Infisical${NC}"

# ── Step 3: Verify project paths ────────────────────────────────────────────
echo ""
echo "Verifying secret paths exist..."

PATHS=(
  "/fabric-4l/value-fabric/dev"
  "/fabric-4l/apps/web/dev"
)

for p in "${PATHS[@]}"; do
  if infisical secrets --env=dev --path="$p" --silent 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} $p"
  else
    echo -e "  ${YELLOW}⚠${NC} $p — path not found or no access (may need project setup)"
  fi
done

# ── Step 4: Print usage ─────────────────────────────────────────────────────
echo ""
echo "============================================="
echo -e "${GREEN}Ready!${NC} Run services with Infisical-injected secrets:"
echo ""
echo "  # Backend"
echo "  infisical run --env=dev --path=/fabric-4l/services/dev -- pnpm dev:backend"
echo ""
echo "  # Frontend"
echo "  infisical run --env=dev --path=/fabric-4l/apps/web/dev -- pnpm --dir apps/web dev"
echo ""
echo "  # Or use package scripts (if configured in root package.json):"
echo "  pnpm dev:backend"
echo "  pnpm dev:frontend"
echo ""
