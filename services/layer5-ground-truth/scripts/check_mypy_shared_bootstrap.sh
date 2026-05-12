#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python -m mypy \
  --ignore-missing-imports \
  --follow-imports=skip \
  src/layer5_ground_truth/shared_bootstrap.py \
  src/layer5_ground_truth/database.py
