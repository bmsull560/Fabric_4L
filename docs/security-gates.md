# Security Gates: DAST + SBOM + Regression

This document explains the CI security gates enforced by `.github/workflows/security-gates.yml` and how to run equivalent checks locally.

## What is gated in CI

The `Security Gates` workflow now includes:

1. **DAST against an ephemeral stack**
   - Starts `docker-compose.full.yml` with local CI-safe environment values.
   - Waits for public health endpoints.
   - Runs OWASP ZAP baseline scans against:
     - `http://127.0.0.1:8001` (Layer 1 API)
     - `http://127.0.0.1:8002` (Layer 2 API)
     - `http://127.0.0.1:8003` (Layer 3 API)
     - `http://127.0.0.1:8004` (Layer 4 API)
     - `http://127.0.0.1:8005` (Layer 5 API)

2. **SBOM generation for each build image artifact**
   - Builds each layer image.
   - Generates a CycloneDX SBOM (`*-sbom.cdx.json`) using Trivy.

3. **SBOM vulnerability policy gate + artifact upload**
   - Scans each SBOM and fails on `HIGH,CRITICAL` vulnerabilities.
   - Uploads SBOM and vulnerability SARIF per artifact.

4. **Mandatory Security Regression Gate** (Sprint 4 enhancement)
   - Runs `scripts/ci/mandatory_security_regression_gate.sh`
   - Includes I-02 production fail-closed tests for Layer 2 and Layer 5
   - Includes tenant boundary, auth regression, and rate limit checks
   - Includes frontend contract guards and critical E2E skip-valve guards
   - Includes Kubernetes hardening checks
   - Fails closed if required suites are missing
   - Evidence written to `fabric_audit/` (repo-relative)
   - See [I-04 Evidence](fabric_audit/i04_mandatory_security_regression_gate_evidence.md)

5. **Release evidence bundle**
   - Collects DAST + SBOM + security scan artifacts.
   - Publishes `release-security-evidence-<sha>` for release/audit evidence.

6. **Required merge gate check**
   - A dedicated PR job named **`Security Gates Required`** depends on:
     - `DAST (OWASP ZAP baseline)`
     - all matrix runs in `SBOM + Policy (...)`
     - `Route Auth Dependency Gate`
     - `Mandatory Security Regression Gate`

## Configure branch protection (required status check)

To prevent merges without DAST, SBOM, route-auth, and mandatory regression success, set branch protection on `main` to require these checks:

- **`Security Gates Required`**
- **`Route Auth Dependency Gate`**
- **`Mandatory Security Regression Gate`**

Recommended:
- Keep `Security Gates` workflow required for pull requests.
- Enable “Require branches to be up to date before merging”.

> Note: GitHub required status checks are repository settings and cannot be fully enforced only from workflow YAML.

## Local runbook for security gates

From repo root:

### 1) Start ephemeral stack

```bash
cd value-fabric
cat > .env << 'EOF'
OPENAI_API_KEY=dummy-key-for-local
ANTHROPIC_API_KEY=dummy-key-for-local
JWT_SECRET=local-jwt-secret
NEO4J_PASSWORD=valuefabric
EOF

docker compose up -d --build
```

### 2) Wait for API health

```bash
for target in \
  "http://localhost:8001/health" \
  "http://localhost:8002/health" \
  "http://localhost:8003/health" \
  "http://localhost:8004/health" \
  "http://localhost:8005/api/v1/health"; do
  until curl -fsS "$target" >/dev/null; do
    sleep 5
  done
  echo "Healthy: $target"
done
```

### 3) Run OWASP ZAP baseline DAST

```bash
mkdir -p ../zap-reports
for target in \
  "layer1:http://127.0.0.1:8001" \
  "layer2:http://127.0.0.1:8002" \
  "layer3:http://127.0.0.1:8003" \
  "layer4:http://127.0.0.1:8004" \
  "layer5:http://127.0.0.1:8005"; do
  name="${target%%:*}"
  url="${target#*:}"
  docker run --rm --network host \
    -v "${PWD}/../zap-reports:/zap/wrk:rw" \
    ghcr.io/zaproxy/zaproxy:stable \
    zap-baseline.py \
    -t "$url" \
    -J "${name}-zap-report.json" \
    -r "${name}-zap-report.html" \
    -w "${name}-zap-warnings.md" \
    -m 5
done
```

### 4) Build images and generate/scan SBOMs

```bash
cd ..
mkdir -p sbom-reports

for layer in \
  layer1-ingestion \
  layer2-extraction \
  layer3-knowledge \
  layer4-agents \
  layer5-ground-truth \
  layer6-benchmarks; do
  docker build -t "${layer}:local" "services/${layer}"

  trivy image --format cyclonedx --output "sbom-reports/${layer}-sbom.cdx.json" "${layer}:local"

  trivy sbom --exit-code 1 --ignore-unfixed \
    --severity HIGH,CRITICAL \
    --format sarif \
    --output "sbom-reports/${layer}-sbom-vuln.sarif" \
    "sbom-reports/${layer}-sbom.cdx.json"
done
```

### 5) Capture release evidence locally

```bash
mkdir -p release-security-evidence
cp -r zap-reports release-security-evidence/
cp -r sbom-reports release-security-evidence/

echo "Security evidence generated at $(date -u +"%Y-%m-%dT%H:%M:%SZ")" > release-security-evidence/SECURITY_EVIDENCE_MANIFEST.md
```

### 6) Teardown

```bash
cd value-fabric
docker compose down -v
```

## Artifacts produced in CI

- `dast-zap-reports` (ZAP JSON/HTML/markdown + compose logs)
- `sbom-<layer>` (CycloneDX SBOM + SBOM vulnerability SARIF)
- `release-security-evidence-<sha>` (aggregate evidence bundle)

These artifacts are suitable to attach to release records and security audit evidence.
