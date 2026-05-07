#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "[1/4] Checking legacy filesystem references..."
python scripts/ci/legacy_path_guard.py --repo-root .

echo "[2/4] Checking repo canonical topology rules..."
python scripts/ci/repo_hygiene.py --repo-root .

echo "[3/4] Verifying service manifests/scripts/tests use canonical services/ paths..."
rg -n "value-fabric/" services scripts tests \
  --glob '!**/*.md' \
  --glob '!**/*.txt' \
  --glob '!**/*.patch' \
  --glob '!**/.venv/**' \
  || true

echo "[4/4] Verifying compatibility import namespace remains resolvable..."
python - <<'PY'
import importlib
importlib.import_module('value_fabric')
importlib.import_module('value_fabric.shared')
print('PASS: compatibility namespace imports resolve')
PY

echo "Migration verification checklist complete."
