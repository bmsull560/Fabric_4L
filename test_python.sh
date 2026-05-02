#!/usr/bin/env bash
GATE_RESULT_REL="artifacts/release/gate-result.json"
_PYTHON="${PYTHON:-python3}"
ADVISORY_TOTAL="$($_PYTHON -c "import json,sys; d=json.load(open('$GATE_RESULT_REL')); print(d.get('advisory_total',0))" 2>/dev/null || echo 0)"
echo "advisory_total=$ADVISORY_TOTAL"
ARTIFACT_PASS="$($_PYTHON -c "import json,sys; d=json.load(open('$GATE_RESULT_REL')); print(d.get('artifact_pass',0))" 2>/dev/null || echo 0)"
echo "artifact_pass=$ARTIFACT_PASS"
