# Deployment Signature and Provenance Verification

## Purpose

This runbook documents how Fabric 4L verifies that each container image was:

1. built by the trusted GitHub Actions workflow,
2. keylessly signed with Sigstore Cosign using GitHub OIDC, and
3. accompanied by a SLSA-compatible provenance attestation.

Deployment **must fail closed** if either signature or attestation verification fails.

## What the CI pipeline publishes

The `build-deploy` workflow publishes, for each layer image:

- tags: `sha-<short_sha>`, `<branch>`, and optional `latest`,
- Cosign signatures for each pushed tag and the immutable digest, and
- a provenance attestation in the registry for the image digest.

Trusted signing identity:

- OIDC issuer: `https://token.actions.githubusercontent.com`
- Certificate identity:
  `https://github.com/<org>/<repo>/.github/workflows/build-deploy.yml@refs/heads/main`

## Deployment gate: verify before pull/apply

Before any deployment pull/apply (Helm, Kustomize, raw manifests, or Terraform), resolve and verify the target image reference.

### 1) Resolve target image reference

Prefer immutable digest refs during deployment:

```bash
IMAGE="ghcr.io/<org>/fabric_4l/layer4-agents@sha256:<digest>"
```

If a tag is supplied by release automation, resolve it first and pin to digest.

### 2) Verify signature

```bash
cosign verify \
  --certificate-identity "https://github.com/<org>/<repo>/.github/workflows/build-deploy.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  "$IMAGE"
```

Expected outcome:

- command exits `0`
- certificate identity matches the trusted workflow path/branch
- certificate OIDC issuer matches GitHub Actions

### 3) Verify provenance attestation

```bash
cosign verify-attestation \
  --type slsaprovenance \
  --certificate-identity "https://github.com/<org>/<repo>/.github/workflows/build-deploy.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  "$IMAGE"
```

Expected outcome:

- command exits `0`
- at least one valid SLSA provenance statement is present for the image digest

### 4) Enforce commit/workflow binding

When promoting a specific release, confirm the attestation and release metadata match:

- expected git commit SHA,
- expected workflow (`.github/workflows/build-deploy.yml`), and
- expected workflow run metadata (run ID / run attempt from CI logs/artifacts).

> Practical check: compare the release's recorded commit SHA with the digest provenance produced in the same workflow run. If these diverge, block deployment.

## Example fail-closed deployment gate script

```bash
#!/usr/bin/env bash
set -euo pipefail

IMAGE="$1"
IDENTITY="https://github.com/<org>/<repo>/.github/workflows/build-deploy.yml@refs/heads/main"
ISSUER="https://token.actions.githubusercontent.com"

cosign verify \
  --certificate-identity "$IDENTITY" \
  --certificate-oidc-issuer "$ISSUER" \
  "$IMAGE" >/dev/null

cosign verify-attestation \
  --type slsaprovenance \
  --certificate-identity "$IDENTITY" \
  --certificate-oidc-issuer "$ISSUER" \
  "$IMAGE" >/dev/null

echo "Verified signature + SLSA provenance for $IMAGE"
```

Use this gate in CD before rendering manifests, before image pull, and before cluster apply.

## Incident response

If verification fails:

1. stop rollout immediately,
2. identify whether the failure is missing signature, bad cert identity, missing attestation, or digest mismatch,
3. inspect the originating GitHub Actions run for the image build,
4. re-build and re-sign from trusted `main` only,
5. re-run verification before retrying deployment.
