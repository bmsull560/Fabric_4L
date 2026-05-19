#!/usr/bin/env bash
# verify-artifact.sh — Verify container image signatures and provenance before deployment
#
# Usage:
#   ./scripts/security/verify-artifact.sh <image-ref> [--oidc-issuer URL] [--cert-identity PATTERN]
#
# Performs:
#   1. Cosign signature verification (keyless / OIDC)
#   2. SLSA provenance attestation verification
#   3. SBOM attestation verification (if present)
#   4. Non-root runtime user check
#   5. Outputs structured JSON verification report
#
# Exit codes:
#   0 — All checks passed
#   1 — One or more checks failed (fail-closed)
set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────
OIDC_ISSUER="https://token.actions.githubusercontent.com"
CERT_IDENTITY_REGEX="https://github.com/bmsull560/Fabric_4L/.github/workflows/build-deploy.yml@.*"
OUTPUT_DIR="artifacts/verification"
REPORT_FILE=""

# ── Argument parsing ─────────────────────────────────────────────────
IMAGE_REF="${1:-}"
shift || true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --oidc-issuer)     OIDC_ISSUER="$2";        shift 2 ;;
    --cert-identity)   CERT_IDENTITY_REGEX="$2"; shift 2 ;;
    --output-dir)      OUTPUT_DIR="$2";          shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$IMAGE_REF" ]]; then
  echo "Usage: $0 <image-ref> [--oidc-issuer URL] [--cert-identity PATTERN] [--output-dir DIR]"
  exit 1
fi

# ── Prerequisites ────────────────────────────────────────────────────
for cmd in cosign docker jq; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: Required tool '${cmd}' is not installed."
    exit 1
  fi
done

mkdir -p "$OUTPUT_DIR"
REPORT_FILE="${OUTPUT_DIR}/verification-$(echo "$IMAGE_REF" | tr '/:@' '___').json"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
FAILURES=0

# ── Helper ───────────────────────────────────────────────────────────
check() {
  local name="$1" result="$2" detail="$3"
  if [[ "$result" == "PASS" ]]; then
    echo "  ✅ ${name}"
  else
    echo "  ❌ ${name}: ${detail}"
    FAILURES=$((FAILURES + 1))
  fi
  CHECKS+=("{\"check\":\"${name}\",\"result\":\"${result}\",\"detail\":\"${detail}\"}")
}

CHECKS=()

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          Artifact Verification — Supply Chain Gate          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Image:    ${IMAGE_REF}"
echo "Issuer:   ${OIDC_ISSUER}"
echo "Identity: ${CERT_IDENTITY_REGEX}"
echo ""

# ── 1. Cosign signature verification ────────────────────────────────
echo "── Signature Verification ──"
if cosign verify \
  --certificate-identity-regexp "$CERT_IDENTITY_REGEX" \
  --certificate-oidc-issuer "$OIDC_ISSUER" \
  "$IMAGE_REF" > "${OUTPUT_DIR}/sig-verify.json" 2>&1; then
  check "Cosign Signature" "PASS" "Signature verified against OIDC identity"
else
  check "Cosign Signature" "FAIL" "Signature verification failed"
fi

# ── 2. SLSA Provenance attestation ──────────────────────────────────
echo "── SLSA Provenance Verification ──"
if cosign verify-attestation \
  --type slsaprovenance \
  --certificate-identity-regexp "$CERT_IDENTITY_REGEX" \
  --certificate-oidc-issuer "$OIDC_ISSUER" \
  "$IMAGE_REF" > "${OUTPUT_DIR}/provenance-verify.json" 2>&1; then
  check "SLSA Provenance" "PASS" "Provenance attestation verified"
else
  check "SLSA Provenance" "FAIL" "Provenance attestation verification failed"
fi

# ── 3. SBOM attestation (optional, warn only) ───────────────────────
echo "── SBOM Attestation Check ──"
if cosign verify-attestation \
  --type cyclonedx \
  --certificate-identity-regexp "$CERT_IDENTITY_REGEX" \
  --certificate-oidc-issuer "$OIDC_ISSUER" \
  "$IMAGE_REF" > "${OUTPUT_DIR}/sbom-verify.json" 2>&1; then
  check "SBOM Attestation" "PASS" "CycloneDX SBOM attestation verified"
else
  # SBOM attestation is informational — does not fail the gate
  echo "  ⚠️  SBOM Attestation: Not found (informational, not blocking)"
  CHECKS+=("{\"check\":\"SBOM Attestation\",\"result\":\"WARN\",\"detail\":\"No CycloneDX attestation found\"}")
fi

# ── 4. Non-root runtime check ───────────────────────────────────────
echo "── Non-Root Runtime Check ──"
CONTAINER_USER=$(docker run --rm --security-opt=no-new-privileges --cap-drop=ALL --entrypoint id "$IMAGE_REF" -u 2>/dev/null || echo "unknown")
if [[ "$CONTAINER_USER" == "0" ]]; then
  check "Non-Root User" "FAIL" "Container runs as root (uid=0)"
elif [[ "$CONTAINER_USER" == "unknown" ]]; then
  check "Non-Root User" "FAIL" "Could not determine container user"
else
  check "Non-Root User" "PASS" "Container runs as uid=${CONTAINER_USER}"
fi

# ── 5. Image digest pinning check ───────────────────────────────────
echo "── Digest Pinning Check ──"
if echo "$IMAGE_REF" | grep -q '@sha256:'; then
  check "Digest Pin" "PASS" "Image referenced by digest"
else
  DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' "$IMAGE_REF" 2>/dev/null || echo "")
  if [[ -n "$DIGEST" ]]; then
    check "Digest Pin" "PASS" "Resolved digest: ${DIGEST}"
  else
    check "Digest Pin" "FAIL" "Image not referenced by digest and digest not resolvable"
  fi
fi

# ── Build verification report ────────────────────────────────────────
echo ""
echo "── Verification Report ──"
CHECKS_JSON=$(printf '%s,' "${CHECKS[@]}" | sed 's/,$//')
cat > "$REPORT_FILE" <<EOF
{
  "image": "${IMAGE_REF}",
  "timestamp": "${TIMESTAMP}",
  "oidc_issuer": "${OIDC_ISSUER}",
  "certificate_identity": "${CERT_IDENTITY_REGEX}",
  "total_checks": ${#CHECKS[@]},
  "failures": ${FAILURES},
  "verdict": "$([ $FAILURES -eq 0 ] && echo PASS || echo FAIL)",
  "checks": [${CHECKS_JSON}]
}
EOF

echo "Report written to: ${REPORT_FILE}"
jq . "$REPORT_FILE"

# ── Fail-closed ──────────────────────────────────────────────────────
if [[ $FAILURES -gt 0 ]]; then
  echo ""
  echo "❌ VERIFICATION FAILED — ${FAILURES} check(s) did not pass."
  echo "   Deployment BLOCKED. Resolve failures before proceeding."
  exit 1
fi

echo ""
echo "✅ ALL CHECKS PASSED — artifact is verified for deployment."
exit 0
