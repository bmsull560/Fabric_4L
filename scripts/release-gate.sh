#!/usr/bin/env bash
# Compatibility wrapper. Canonical release gate lives in scripts/ops/.
set -euo pipefail

echo "[compat] scripts/release-gate.sh is deprecated; forwarding to scripts/ops/release-gate.sh" >&2
bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/ops/release-gate.sh" "$@"
