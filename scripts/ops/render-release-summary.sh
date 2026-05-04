#!/usr/bin/env bash
# scripts/render-release-summary.sh — Enforcement-grade release summary renderer
set -euo pipefail

_PYTHON="${PYTHON:-python3}"
if ! command -v "$_PYTHON" > /dev/null 2>&1; then
    _PYTHON="python"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ARTIFACT_DIR="${ROOT}/artifacts/release"
LOG_DIR="${ARTIFACT_DIR}/logs"
POLICY_FILE="${ROOT}/.fabric/prod-gates.policy.yaml"
mkdir -p "$LOG_DIR"

SUMMARY="${ARTIFACT_DIR}/summary.md"
GIT_SHA="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
GIT_BRANCH="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u +%Y-%m-%dT%H:%M:%SZ)"
POLICY_HASH="$(sha256sum "$POLICY_FILE" 2>/dev/null | cut -d' ' -f1 || echo 'unknown')"

# Parse profile from log if available
PROFILE="release-candidate"
if [ -s "$LOG_DIR/release-gate.log" ]; then
    PROFILE_LINE="$(grep -m1 "Release Gate — Profile:" "$LOG_DIR/release-gate.log" || true)"
    if [ -n "$PROFILE_LINE" ]; then
        PROFILE="$(echo "$PROFILE_LINE" | sed 's/.*Profile: //')"
    fi
fi

# Determine overall status from gate-result.json if available, else fall back to log parsing
FINAL_DECISION="🟡 INCONCLUSIVE"
FAIL_REASONS=""
BLOCKING_PASS=0
BLOCKING_TOTAL=0
ADVISORY_PASS=0
ADVISORY_TOTAL=0
ARTIFACT_PASS=0
ARTIFACT_TOTAL=0
PLACEHOLDER_FAIL=0
NEGATIVE_PASS=0
NEGATIVE_TOTAL=0

GATE_RESULT_REL="artifacts/release/gate-result.json"
if [ -s "$GATE_RESULT_REL" ]; then
    FINAL_DECISION="$($_PYTHON -c "import json,sys; d=json.load(open('$GATE_RESULT_REL')); print(d.get('decision','INCONCLUSIVE'))" 2>/dev/null || echo 'INCONCLUSIVE')"
    FAIL_REASONS="$($_PYTHON -c "import json,sys; d=json.load(open('$GATE_RESULT_REL')); print(d.get('fail_reasons',''))" 2>/dev/null || echo '')"
    BLOCKING_PASS="$($_PYTHON -c "import json,sys; d=json.load(open('$GATE_RESULT_REL')); print(d.get('blocking_pass',0))" 2>/dev/null || echo 0)"
    BLOCKING_TOTAL="$($_PYTHON -c "import json,sys; d=json.load(open('$GATE_RESULT_REL')); print(d.get('blocking_total',0))" 2>/dev/null || echo 0)"
    ADVISORY_PASS="$($_PYTHON -c "import json,sys; d=json.load(open('$GATE_RESULT_REL')); print(d.get('advisory_pass',0))" 2>/dev/null || echo 0)"
    ADVISORY_TOTAL="$($_PYTHON -c "import json,sys; d=json.load(open('$GATE_RESULT_REL')); print(d.get('advisory_total',0))" 2>/dev/null || echo 0)"
    ARTIFACT_PASS="$($_PYTHON -c "import json,sys; d=json.load(open('$GATE_RESULT_REL')); print(d.get('artifact_pass',0))" 2>/dev/null || echo 0)"
    ARTIFACT_TOTAL="$($_PYTHON -c "import json,sys; d=json.load(open('$GATE_RESULT_REL')); print(d.get('artifact_total',0))" 2>/dev/null || echo 0)"
    PLACEHOLDER_FAIL="$($_PYTHON -c "import json,sys; d=json.load(open('$GATE_RESULT_REL')); print(d.get('placeholder_fail',0))" 2>/dev/null || echo 0)"
    NEGATIVE_PASS="$($_PYTHON -c "import json,sys; d=json.load(open('$GATE_RESULT_REL')); print(d.get('negative_pass',0))" 2>/dev/null || echo 0)"
    NEGATIVE_TOTAL="$($_PYTHON -c "import json,sys; d=json.load(open('$GATE_RESULT_REL')); print(d.get('negative_total',0))" 2>/dev/null || echo 0)"
elif [ -s "$LOG_DIR/release-gate.log" ]; then
    if grep -q "PASS — All blocking gates passed" "$LOG_DIR/release-gate.log"; then
        FINAL_DECISION="PASS"
    elif grep -q "FAIL —" "$LOG_DIR/release-gate.log"; then
        FINAL_DECISION="FAIL"
        FAIL_REASONS="$(grep "FAIL —" "$LOG_DIR/release-gate.log" | sed 's/.*FAIL — //')"
    fi
fi

# Build gate results table from log and policy metadata
GATE_TABLE=""
ACCEPTED_CAVEATS=""
SKIPPED_CHECKS=""

if [ -s "$LOG_DIR/policy-meta.txt" ] && [ -s "$LOG_DIR/release-gate.log" ]; then
    # Parse gate metadata
    declare -A META_CLASS
    declare -A META_CAVEAT
    while IFS= read -r line; do
        if [[ "$line" == GATE:* ]]; then
            IFS=':' read -r _ gate target klass required artifact_dir caveat <<< "$line"
            META_CLASS[$gate]="$klass"
            META_CAVEAT[$gate]="$caveat"
        fi
    done < "$LOG_DIR/policy-meta.txt"

    # Parse gate statuses from log
    declare -A LOG_STATUS
    declare -A LOG_REASON
    while IFS= read -r line; do
        if echo "$line" | grep -qE '^   ✅'; then
            gate="$(echo "$line" | sed -E 's/^   ✅ (.*)/\1/')"
            LOG_STATUS[$gate]="PASS"
        elif echo "$line" | grep -qE '^   ❌'; then
            gate="$(echo "$line" | sed -E 's/^   ❌ ([^ ]+).*/\1/')"
            LOG_STATUS[$gate]="FAIL"
            if echo "$line" | grep -q "PLACEHOLDER"; then
                LOG_REASON[$gate]="PLACEHOLDER"
            fi
        fi
    done < "$LOG_DIR/release-gate.log"

    for gate in "${!META_CLASS[@]}"; do
        klass="${META_CLASS[$gate]}"
        status="${LOG_STATUS[$gate]:-NOT_RUN}"
        caveat="${META_CAVEAT[$gate]}"
        reason="${LOG_REASON[$gate]:-}"

        if [ "$status" = "PASS" ]; then
            GATE_TABLE="${GATE_TABLE}| $gate | ✅ PASS | $klass | — |\n"
        elif [ "$status" = "FAIL" ]; then
            if [ "$klass" = "placeholder" ]; then
                GATE_TABLE="${GATE_TABLE}| $gate | ❌ FAIL | $klass | Placeholder — not implemented |\n"
                ACCEPTED_CAVEATS="${ACCEPTED_CAVEATS}- **$gate**: $caveat\n"
            elif [ "$klass" = "advisory" ]; then
                GATE_TABLE="${GATE_TABLE}| $gate | ⚠️ FAIL | $klass | $caveat |\n"
                ACCEPTED_CAVEATS="${ACCEPTED_CAVEATS}- **$gate** (advisory): $caveat\n"
            else
                GATE_TABLE="${GATE_TABLE}| $gate | ❌ FAIL | $klass | $reason |\n"
            fi
        else
            GATE_TABLE="${GATE_TABLE}| $gate | ⏳ NOT_RUN | $klass | — |\n"
            SKIPPED_CHECKS="${SKIPPED_CHECKS}- $gate\n"
        fi
    done
else
    GATE_TABLE="| (no gate log found) | ⏳ | — | Run release-gate.sh first |\n"
fi

# List generated artifacts
ARTIFACT_LIST=""
ARTIFACT_COUNT=0
if [ -d "$ARTIFACT_DIR" ]; then
    # Use a temp file instead of process substitution for broader shell compatibility
    # Clean any stale temp files first
    rm -f "${LOG_DIR}/.artifacts.tmp"
    _artifact_list_file="${LOG_DIR}/.artifacts.tmp"
    find "$ARTIFACT_DIR" -type f 2>/dev/null | sort > "$_artifact_list_file"
    while IFS= read -r f; do
        rel="$(realpath --relative-to="$ARTIFACT_DIR" "$f" 2>/dev/null || echo "$f")"
        size="$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f" 2>/dev/null || echo '?')"
        ARTIFACT_LIST="${ARTIFACT_LIST}- \`${rel}\` (${size} bytes)\n"
        ARTIFACT_COUNT=$((ARTIFACT_COUNT + 1))
    done < "$_artifact_list_file"
    rm -f "$_artifact_list_file"
else
    ARTIFACT_LIST="- (no artifacts generated)\n"
fi

# Format decision emoji
DECISION_EMOJI="🟡"
if [ "$FINAL_DECISION" = "PASS" ]; then
    DECISION_EMOJI="🟢"
elif [ "$FINAL_DECISION" = "FAIL" ]; then
    DECISION_EMOJI="🔴"
fi

cat > "$SUMMARY" <<EOF
# Value Fabric — Release Gate Summary

| Field            | Value                                          |
|------------------|------------------------------------------------|
| Timestamp        | ${TS}                                          |
| Git SHA          | \`${GIT_SHA}\`                                 |
| Branch           | ${GIT_BRANCH}                                  |
| Profile          | ${PROFILE}                                     |
| Final Decision   | ${DECISION_EMOJI} ${FINAL_DECISION}            |
| Policy File      | \`${POLICY_FILE}\`                             |
| Policy SHA-256   | \`${POLICY_HASH}\`                             |

## Gate Results

| Gate | Status | Class | Notes |
|------|--------|-------|-------|
${GATE_TABLE}

## Scorecard

| Category    | Result |
|-------------|--------|
| Blocking    | ${BLOCKING_PASS}/${BLOCKING_TOTAL} passed |
| Advisory    | ${ADVISORY_PASS}/${ADVISORY_TOTAL} passed |
| Artifact    | ${ARTIFACT_PASS}/${ARTIFACT_TOTAL} passed |
| Placeholder | ${PLACEHOLDER_FAIL} failed (release-candidate blocks) |
| Negative    | ${NEGATIVE_PASS}/${NEGATIVE_TOTAL} checks validated |

## Blocking Checks

Blocking gates must pass for any profile. A failure here blocks release unconditionally.

## Advisory Checks

Advisory gates run and report results but do not block release. They signal areas
needing attention (missing services, optional dependencies, environment gaps).

## Placeholder / Skipped Checks

Placeholder gates are explicitly not implemented. In \`release-candidate\` profile,
these block release to prevent silent gaps. In \`pr-fast\`, they are omitted.

## Generated Artifacts

(${ARTIFACT_COUNT} files)

${ARTIFACT_LIST}

## Skipped Checks

${SKIPPED_CHECKS:-None}

## Accepted Caveats

${ACCEPTED_CAVEATS:-None}

## Failure Reasons

${FAIL_REASONS:-None}

## Known System Caveats

- **Release-candidate placeholders**: no unclassified release-candidate placeholder gates are allowed; chaos and release-policy are implemented blocking gates.
- **Advisory gates**: smoke, agent, and obs remain advisory where they require live services or optional dependencies.
- **Controlled Pilot vs Broad GA**: this summary supports Controlled Pilot evidence unless the full release gate and all broad-GA dependencies have passing artifacts.
- **Launch blockers**: any failing blocking gate or missing artifact must remain classified in the gate logs and release summary rather than being marked complete.

## Verification

To reproduce this gate run:

\`\`\`bash
make release-gate PROFILE=${PROFILE}
\`\`\`

---
*Generated by \`scripts/render-release-summary.sh\`*
EOF

echo "   📄  Summary written to $SUMMARY"
