#!/usr/bin/env bash
# Tests for placeholder digest detection in prepare_kustomize_deploy.sh.
# Run with: bash scripts/ci/test_placeholder_digest_detection.sh
set -euo pipefail

PASS=0
FAIL=0

_assert() {
  local desc="$1"
  local expected="$2"
  local actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "  PASS: $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $desc (expected=$expected, actual=$actual)"
    FAIL=$((FAIL + 1))
  fi
}

# Mirror the helper function from prepare_kustomize_deploy.sh
_is_placeholder_digest() {
  local digest="${1#sha256:}"
  [[ ${#digest} -eq 64 ]] || return 1
  if echo "$digest" | grep -qP '^([0-9a-f])\1{63}$' 2>/dev/null; then
    return 0
  fi
  local first="${digest:0:1}"
  local repeated
  repeated="$(printf '%0.s'"$first" {1..64})"
  [[ "$digest" == "$repeated" ]]
}

echo "--- Placeholder digest detection ---"

# Should be detected as placeholders
for d in \
  "sha256:1111111111111111111111111111111111111111111111111111111111111111" \
  "sha256:2222222222222222222222222222222222222222222222222222222222222222" \
  "sha256:7777777777777777777777777777777777777777777777777777777777777777" \
  "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
  "sha256:0000000000000000000000000000000000000000000000000000000000000000"
do
  if _is_placeholder_digest "$d"; then
    _assert "detects $d" "placeholder" "placeholder"
  else
    _assert "detects $d" "placeholder" "real"
  fi
done

# Should NOT be detected as placeholders (real-looking digests)
for d in \
  "sha256:a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2" \
  "sha256:deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef" \
  "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
do
  if _is_placeholder_digest "$d"; then
    _assert "passes $d" "real" "placeholder"
  else
    _assert "passes $d" "real" "real"
  fi
done

echo ""
echo "--- Grep pattern test against prod kustomization.yaml ---"
KUSTOMIZATION="k8s/envs/prod/kustomization.yaml"
if [[ -f "$KUSTOMIZATION" ]]; then
  # Placeholder digests must NOT be present in the committed kustomization.yaml.
  # Digests are injected at deploy time by prepare_kustomize_deploy.sh.
  if grep -Eq 'sha256:([0-9a-f])\1{63}' "$KUSTOMIZATION"; then
    _assert "prod kustomization has no placeholder digests" "clean" "has-placeholders"
  else
    _assert "prod kustomization has no placeholder digests" "clean" "clean"
  fi
else
  echo "  SKIP: $KUSTOMIZATION not found (run from repo root)"
fi

echo ""
echo "Results: ${PASS} passed, ${FAIL} failed"
[[ $FAIL -eq 0 ]]
