# Supply Chain Integrity Documentation

## Overview

Value Fabric implements SLSA 3 supply chain integrity using:
- **Keyless signing** via Sigstore Cosign with GitHub Actions OIDC
- **SBOM generation** in CycloneDX and SPDX formats
- **SLSA provenance** attestations for build verification
- **Admission policies** via Kyverno for runtime enforcement

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     BUILD PIPELINE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │   Docker     │──▶│   Cosign     │──▶│    SBOM      │    │
│  │    Build     │   │   Sign       │   │  (Syft)      │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│                             │                             │
│                             ▼                             │
│                      ┌──────────────┐                      │
│                      │   Rekor      │                      │
│                      │  (Sigstore)  │                      │
│                      └──────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │   Kyverno    │──▶│   Verify     │──▶│   Deploy     │    │
│  │   Policy     │   │  Signature   │   │   Pod        │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│                                                             │
│  Policies:                                                  │
│  - verify-image-signatures                                  │
│  - require-sbom-attestation                                 │
│  - verify-slsa-provenance                                   │
│  - block-latest-tag                                         │
│  - require-image-digest                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## SLSA Compliance

| Level | Requirement | Implementation |
|-------|-------------|----------------|
| L1 | Provenance exists | ✅ SLSA provenance generated |
| L2 | Signed provenance | ✅ Cosign keyless signing |
| L3 | Trusted builder | ✅ GitHub Actions with OIDC |
| L4 | Hermetic builds | ⚠️ Partial (network access for deps) |

## Verification

### Verify Image Signatures

```bash
# Single image
cosign verify \
  --certificate-identity-regexp="https://github.com/bmsull560/Fabric_4L/.github/workflows/.*" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  ghcr.io/bmsull560/fabric_4l/layer1-ingestion:sha-abc123

# All images
./scripts/security/verify-supply-chain.sh sha-abc123
```

### Verify SBOM Attestation

```bash
# Download and verify SBOM
cosign verify-attestation \
  --type cyclonedx \
  --certificate-identity-regexp="https://github.com/bmsull560/Fabric_4L/.github/workflows/.*" \
  ghcr.io/bmsull560/fabric_4l/layer1-ingestion:sha-abc123 \
  | jq -r '.payload' | base64 -d | jq
```

### Verify SLSA Provenance

```bash
cosign verify-attestation \
  --type slsaprovenance \
  --certificate-identity-regexp="https://github.com/bmsull560/Fabric_4L/.github/workflows/.*" \
  ghcr.io/bmsull560/fabric_4l/layer1-ingestion:sha-abc123
```

## Workflows

### Build and Sign (`.github/workflows/build-deploy.yml`)

1. Builds container images
2. Signs with Cosign (keyless OIDC)
3. Pushes to registry

### Supply Chain (`.github/workflows/supply-chain.yml`)

1. Generates SBOMs (CycloneDX + SPDX)
2. Scans for vulnerabilities (Grype)
3. Generates SLSA provenance
4. Verifies signatures
5. Audits dependencies

### Package and Sign (`.github/workflows/package-sign.yml`)

1. Signs images with Cosign
2. Generates SBOMs
3. Creates attestation bundles

## Admission Policies

### Installation

```bash
# Install Kyverno
kubectl apply -f https://github.com/kyverno/kyverno/releases/download/v1.11.0/install.yaml

# Apply policies
kubectl apply -f k8s/policy/kyverno-verify-signatures.yaml
kubectl apply -f k8s/policy/kyverno-slsa-provenance.yaml
```

### Policy Summary

| Policy | Action | Severity |
|--------|--------|----------|
| `verify-image-signatures` | Enforce | Critical |
| `require-sbom-attestation` | Enforce | High |
| `verify-slsa-provenance` | Enforce | Critical |
| `block-latest-tag` | Enforce | Medium |
| `require-image-digest` | Audit | Medium |
| `restrict-registries` | Enforce | High |

## Troubleshooting

### Signature Verification Failed

```bash
# Check Rekor entry
cosign verify \
  --certificate-identity-regexp="https://github.com/bmsull560/Fabric_4L/.github/workflows/.*" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  --rekor-url https://rekor.sigstore.dev \
  <image>
```

### Policy Violation

```bash
# Check Kyverno events
kubectl get events --field-selector reason=PolicyViolation

# Check policy reports
kubectl get policyreport -A
```

## Compliance Evidence

### SLSA 3 Attestation

Attestations are stored in Rekor and can be verified via:
- Transparency log: https://rekor.sigstore.dev
- Search: https://search.sigstore.dev

### SBOM Registry

SBOMs are attached as OCI artifacts and can be downloaded:

```bash
# List attestations
cosign tree ghcr.io/bmsull560/fabric_4l/layer1-ingestion:sha-abc123

# Download SBOM
cosign download attestation \
  --predicate-type=https://cyclonedx.org/bom \
  ghcr.io/bmsull560/fabric_4l/layer1-ingestion:sha-abc123
```

## References

- [SLSA Framework](https://slsa.dev/)
- [Sigstore Cosign](https://docs.sigstore.dev/cosign/)
- [CycloneDX](https://cyclonedx.org/)
- [SPDX](https://spdx.dev/)
- [Kyverno](https://kyverno.io/)

## Build/Promotion Metadata Contract Guard

CI enforces a shared build metadata schema between `.github/workflows/build-deploy.yml` and `.github/workflows/environment-promotion.yml` via `scripts/ci/validate_promotion_artifact_contract.py` and `tests/ci/test_build_promotion_artifact_contract.py`. This prevents promotion tag/digest format drift by requiring the emitted `layer`, `image_digest`, `published_tag`, and `source_commit_sha` keys and by verifying promotion consumes digest references from the build artifact contract.
