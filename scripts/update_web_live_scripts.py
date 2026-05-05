#!/usr/bin/env python3
"""Update apps/web package.json with fail-closed live validation scripts."""
from __future__ import annotations

import json
from pathlib import Path

package_path = Path(__file__).resolve().parents[1] / "apps" / "web" / "package.json"
package = json.loads(package_path.read_text())
scripts = package.setdefault("scripts", {})

live_dev_env = " ".join([
    "PLAYWRIGHT_LIVE_MODE=true",
    "VITE_USE_MOCKS=false",
    "VITE_ENABLE_MOCK_FALLBACK=false",
    "VITE_API_BASE=/api/v1",
    "VITE_API_BASE_URL=${VITE_API_BASE_URL:-http://localhost:8004}",
    "VITE_PROXY_L1_URL=${VITE_PROXY_L1_URL:-http://localhost:8001}",
    "VITE_PROXY_L2_URL=${VITE_PROXY_L2_URL:-http://localhost:8002}",
    "VITE_PROXY_L3_URL=${VITE_PROXY_L3_URL:-http://localhost:8003}",
    "VITE_PROXY_L4_URL=${VITE_PROXY_L4_URL:-http://localhost:8004}",
    "VITE_PROXY_L5_URL=${VITE_PROXY_L5_URL:-http://localhost:8005}",
    "VITE_PROXY_L6_URL=${VITE_PROXY_L6_URL:-http://localhost:8006}",
])

scripts["dev:live"] = (
    f"sh -lc '{live_dev_env} node scripts/live-env-guard.mjs dev && "
    f"{live_dev_env} vite --host 0.0.0.0 --port 3001'"
)
scripts["seed:live"] = (
    "sh -lc ': \"${PLAYWRIGHT_BACKEND_URL:?Set PLAYWRIGHT_BACKEND_URL=http://localhost:8004}\"; "
    "PLAYWRIGHT_LIVE_MODE=true VITE_USE_MOCKS=false VITE_ENABLE_MOCK_FALLBACK=false "
    "node scripts/live-env-guard.mjs seed && "
    "PLAYWRIGHT_LIVE_MODE=true VITE_USE_MOCKS=false VITE_ENABLE_MOCK_FALLBACK=false "
    "npx tsx ../../scripts/db/seed-e2e-data.ts --base-url=\"$PLAYWRIGHT_BACKEND_URL\"'"
)

scripts["test:e2e:live"] = (
    "sh -lc ': \"${PLAYWRIGHT_LIVE_MODE:?Set PLAYWRIGHT_LIVE_MODE=true}\"; "
    ": \"${PLAYWRIGHT_LIVE_FRONTEND_URL:?Set PLAYWRIGHT_LIVE_FRONTEND_URL=http://localhost:3001}\"; "
    ": \"${PLAYWRIGHT_BACKEND_URL:?Set PLAYWRIGHT_BACKEND_URL=http://localhost:8004}\"; "
    "VITE_USE_MOCKS=false VITE_ENABLE_MOCK_FALLBACK=false node scripts/live-env-guard.mjs test && "
    "VITE_USE_MOCKS=false VITE_ENABLE_MOCK_FALLBACK=false PLAYWRIGHT_BASE_URL=\"$PLAYWRIGHT_LIVE_FRONTEND_URL\" "
    "pnpm run test:e2e:backend'"
)
scripts["test:e2e:live:p0"] = (
    "sh -lc ': \"${PLAYWRIGHT_LIVE_MODE:?Set PLAYWRIGHT_LIVE_MODE=true}\"; "
    ": \"${PLAYWRIGHT_LIVE_FRONTEND_URL:?Set PLAYWRIGHT_LIVE_FRONTEND_URL=http://localhost:3001}\"; "
    ": \"${PLAYWRIGHT_BACKEND_URL:?Set PLAYWRIGHT_BACKEND_URL=http://localhost:8004}\"; "
    "VITE_USE_MOCKS=false VITE_ENABLE_MOCK_FALLBACK=false node scripts/live-env-guard.mjs test && "
    "VITE_USE_MOCKS=false VITE_ENABLE_MOCK_FALLBACK=false PLAYWRIGHT_BASE_URL=\"$PLAYWRIGHT_LIVE_FRONTEND_URL\" "
    "pnpm run test:e2e:guard && playwright test --project=backend-integrated "
    "e2e/journeys/j7-value-realization-and-calculation.spec.ts "
    "e2e/journeys/j8-approval-review-gates.spec.ts "
    "e2e/journeys/j9-agent-grounding-governance.spec.ts "
    "e2e/journeys/j10-layer-ui-validation.spec.ts "
    "e2e/journeys/j11-golden-path-business-lifecycle.spec.ts "
    "e2e/security/tenant-isolation-validation.spec.ts e2e/export-workflows.spec.ts'"
)
scripts["test:e2e:live:golden-path"] = (
    "sh -lc ': \"${PLAYWRIGHT_LIVE_MODE:?Set PLAYWRIGHT_LIVE_MODE=true}\"; "
    ": \"${PLAYWRIGHT_LIVE_FRONTEND_URL:?Set PLAYWRIGHT_LIVE_FRONTEND_URL=http://localhost:3001}\"; "
    ": \"${PLAYWRIGHT_BACKEND_URL:?Set PLAYWRIGHT_BACKEND_URL=http://localhost:8004}\"; "
    "VITE_USE_MOCKS=false VITE_ENABLE_MOCK_FALLBACK=false node scripts/live-env-guard.mjs test && "
    "VITE_USE_MOCKS=false VITE_ENABLE_MOCK_FALLBACK=false PLAYWRIGHT_BASE_URL=\"$PLAYWRIGHT_LIVE_FRONTEND_URL\" "
    "pnpm run test:e2e:guard && playwright test --project=backend-integrated "
    "e2e/journeys/j1-golden-path-backend-integrated.spec.ts "
    "e2e/journeys/j11-golden-path-business-lifecycle.spec.ts'"
)

package_path.write_text(json.dumps(package, indent=2) + "\n")
print(f"updated {package_path}")
