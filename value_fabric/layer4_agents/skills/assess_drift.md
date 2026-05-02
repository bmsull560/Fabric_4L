---
name: assess_drift
description: Multi-layer drift detection for API contracts, schemas, and behavior drift
allowed_agents: ["system-health", "ci-cd", "devops"]
---

# Assess Drift Skill

## Purpose

Detect and report drift across system boundaries before it causes integration failures. This skill automates the detection of:
- API contract drift (OpenAPI vs implementation)
- Frontend/backend type misalignment
- Database schema evolution drift
- Cross-layer integration contract violations

## When to Use

- Before releases to catch breaking changes
- After cross-layer refactors
- When integration tests fail unexpectedly
- Weekly automated health checks

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| drift_types | string[] | No | ["all"] | Types: openapi, frontend_backend, schema, cross_layer |
| layers | string[] | No | ["all"] | Layers: L1, L2, L3, L4, frontend |
| severity_threshold | string | No | "warning" | Minimum severity: critical, warning, info |
| output_format | string | No | "markdown" | Output: markdown, json, both |
| fail_on_critical | boolean | No | true | Fail if critical drift detected |

## Steps

1. **Run contract tests** (`pytest tests/contract/`)
2. **Regenerate OpenAPI** (`scripts/export_openapi.py`)
3. **Compare frontend hooks** to OpenAPI schemas
4. **Run integration tests** (`pytest tests/integration/`)
5. **Check schema alignment** (migrations vs models)
6. **Generate severity-classified report**

## Output

Structured drift report with:
- Drift type classification
- Severity level (critical/warning/info)
- Location and description
- Expected vs actual comparison
- Remediation guidance

## Example Usage

```bash
# Full assessment
python -m layer4_agents.tools.assess_drift --layers all --drift-types all

# Frontend/backend only
python -m layer4_agents.tools.assess_drift --layers frontend,L3 --drift-types frontend_backend

# CI gate (fails on critical)
python -m layer4_agents.tools.assess_drift --fail-on-critical --output-format json
```

## Safety Notes

- Critical drift must be fixed before production deploy
- Always regenerate OpenAPI after route/schema changes
- Document intentional breaking changes in CHANGELOG.md
