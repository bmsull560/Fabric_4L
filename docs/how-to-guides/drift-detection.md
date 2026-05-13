---
title: "Drift Detection Guide"
category: "how-to"
audience: "developers"
last-reviewed: "2026-05-06"
freshness: "current"
related: ["../core-concepts/architecture.md", "../troubleshooting/index.md", "../../.windsurf/workflows/fumadocs-drift-audit.md"]
---

# Drift Detection Guide

This guide explains how to detect and prevent drift between code, contracts, schemas, and documentation in the Value Fabric platform.

## Overview

Drift occurs when implementation changes outpace documentation updates, or when API contracts no longer match the actual code. Value Fabric provides multiple automated mechanisms to detect drift:

- **CI/CD Workflows**: Automatic drift detection on pull requests and pushes
- **Drift Assessor Agent**: Autonomous architectural drift detection
- **Fumadocs Drift Audit**: Manual workflow for documentation drift audits

## Types of Drift Detected

### API Contract Drift

**What it is**: OpenAPI specifications in `contracts/openapi/` no longer match the actual FastAPI route implementations.

**Detection**: Automatically detected by CI workflows when you change API routes.

**Impact**: Breaking changes to client integrations, incorrect API documentation.

**Fix**: Regenerate OpenAPI specs:
```bash
python scripts/export_openapi.py
git add contracts/openapi/
git commit -m "chore: update openapi contracts"
```

### Generated API Client Drift

**What it is**: Frontend TypeScript API clients in `apps/web/src/api/generated/` are stale compared to the OpenAPI specs.

**Detection**: Automatically detected by CI workflows when you change backend APIs.

**Impact**: TypeScript compilation errors, runtime API call failures.

**Fix**: Regenerate frontend API clients:
```bash
cd apps/web
pnpm run generate:api
git add apps/web/src/api/generated/
git commit -m "chore: regenerate api clients"
```

### Schema Drift

**What it is**: Pydantic models in code diverge from database migrations or JSON Schema definitions.

**Detection**: Detected by the Drift Assessor agent during scheduled assessments.

**Impact**: Data validation failures, database constraint violations.

**Fix**: Align models with migrations and update JSON Schemas in `contracts/jsonschema/`.

### Documentation Drift

**What it is**: Documentation in `docs/` no longer reflects actual code behavior, component props, or API responses.

**Detection**: 
- Manual: Run the Fumadocs Drift Audit workflow
- Autonomous: Drift Assessor agent checks documentation staleness

**Impact**: Developer confusion, incorrect onboarding, wasted debugging time.

**Fix**: Update documentation to match current implementation.

## CI/CD Workflows

### Contract Drift Check

**File**: `.github/workflows/drift-check.yml`

**Triggers**: Pull requests affecting API routes or main files

**What it does**:
1. Exports current OpenAPI specs from all layers
2. Compares against committed specs in `contracts/openapi/`
3. Fails if drift detected

**Failure message**:
```
Contract drift detected! Run 'python scripts/export_openapi.py' locally and commit changes.
```

### OpenAPI Drift Check

**File**: `.github/workflows/openapi-drift-check.yml`

**Triggers**: Pull requests and pushes to API routes

**What it does**:
1. Validates OpenAPI JSON syntax for all layers
2. Checks for spec drift against committed versions
3. Runs contract validation tests

**Layers checked**: Layer 1 (Ingestion), Layer 2 (Extraction), Layer 3 (Knowledge), Layer 4 (Agents), Layer 5 (Ground Truth)

### Generated API Freshness

**File**: `.github/workflows/generated-api-freshness.yml`

**Triggers**: Pull requests and pushes affecting backend APIs or frontend generation scripts

**What it does**:
1. Runs the repository-owned contract gate in fast mode on pull requests and full mode on merge/release branches
2. Regenerates OpenAPI plus TypeScript outputs together
3. Fails on committed drift or incompatible frontend type usage for touched APIs

**Failure message**:
```
Generated API client files are stale.
To fix locally:
  pnpm run generate:contracts
  pnpm run check:contract-compliance -- --mode fast
```

## Drift Assessor Agent

**Location**: `.windsurf/agents/drift-assessor/AGENT.md`

**Purpose**: Autonomous agent that detects architectural drift across API contracts, schemas, frontend/backend alignment, and documentation.

**Capabilities**:
- API contract drift detection (OpenAPI diff vs implementation)
- Schema drift detection (Pydantic model vs DB migration)
- Frontend-backend drift detection (Hook count vs endpoint count)
- Documentation drift detection (via `docs-mcp.check_api_reference`)
- UI drift detection (Fabric UI primitive audit)

**Usage**:
- **Scheduled**: Runs weekly as autonomous assessment
- **On-demand**: Triggered before releases
- **Pipeline**: Stage = `audit`, Output = go/no-go recommendation

**Side-Effect Policy**: Read-only - the agent detects and reports but does not modify files.

## Fumadocs Drift Audit Workflow

**Location**: `.windsurf/workflows/fumadocs-drift-audit.md`

**Purpose**: Manual workflow for auditing Fumadocs-based documentation to detect drift between code implementation and documentation.

**When to Use**:
- Post-release after code changes affecting routes, layouts, or components
- Periodic maintenance (monthly/quarterly documentation health checks)
- Pre-migration before migrating documentation to Fumadocs
- When docs appear out of sync with UI or API behavior
- After upgrading Fumadocs packages

**Workflow Steps**:
1. Locate baseline commit (last known good docs state)
2. Diff from baseline to HEAD
3. Map impact areas (layout, navigation, MDX components, etc.)
4. Check Diátaxis-Fumadocs alignment
5. Collect topic documentation inventory
6. Cross-check docs against code
7. Produce remediation pack with prioritized findings

**Output**: Structured report with:
- Executive summary of drift instances
- Prioritized findings (stale commands, component names, file paths, routes)
- Exact files to update with priority levels
- Draft markdown for top fixes

## When to Run Drift Detection

### Before Releases

Run drift detection as part of your pre-release checklist:
1. Ensure all CI drift checks pass
2. Trigger Drift Assessor agent for full architectural drift assessment
3. Run Fumadocs Drift Audit if documentation changed significantly

### After Major Refactors

After refactoring APIs, schemas, or components:
1. Regenerate OpenAPI specs: `python scripts/export_openapi.py`
2. Regenerate frontend clients: `pnpm run generate:api`
3. Update affected documentation
4. Run Drift Assessor agent to verify no unintended drift

### During Development

Before pushing changes:
```bash
# Required for API contract and generated-client changes
pnpm run generate:contracts
pnpm run check:contract-compliance -- --mode fast

# Use the full gate before merge/release work
pnpm run check:contract-compliance
```

## Troubleshooting

### CI Fails with Contract Drift

**Symptom**: Pull request fails with "Contract drift detected!"

**Cause**: You changed API routes but didn't update OpenAPI specs.

**Fix**:
```bash
pnpm run generate:contracts
pnpm run check:contract-compliance -- --mode fast
git add contracts/openapi/ packages/platform-contract/src/typescript/generated/ apps/web/src/api/generated/
git commit -m "chore: refresh generated contracts"
```

### CI Fails with Generated API Drift

**Symptom**: Pull request fails with "Generated API client files are stale."

**Cause**: You changed backend APIs but didn't regenerate frontend clients.

**Fix**:
```bash
pnpm run generate:contracts
pnpm run check:contract-compliance -- --mode fast
git add packages/platform-contract/src/typescript/generated/ apps/web/src/api/generated/
git commit -m "chore: refresh generated api artifacts"
```

### Documentation Appears Outdated

**Symptom**: Documentation describes features that don't exist or behavior that changed.

**Cause**: Code evolved without documentation updates.

**Fix**:
1. Run Fumadocs Drift Audit workflow: `/fumadocs-drift-audit`
2. Review the remediation pack output
3. Update documentation based on prioritized findings
4. Update `last-reviewed` date in document frontmatter

### Drift Assessor Reports Issues

**Symptom**: Drift Assessor agent reports drift in scheduled assessment.

**Cause**: Unintended changes to contracts, schemas, or alignment.

**Fix**:
1. Review the drift assessment report
2. Determine if drift is intentional (breaking change) or accidental
3. If intentional: update contracts and documentation accordingly
4. If accidental: revert or fix the implementation

## Best Practices

1. **Always run drift checks before merging** - Don't bypass CI drift gates
2. **Update docs with code** - Make documentation updates part of the same PR as code changes
3. **Use semantic versioning** - Document breaking changes in CHANGELOG.md
4. **Review drift reports weekly** - Don't let drift accumulate
5. **Keep contracts as source of truth** - OpenAPI specs should match implementation exactly

## Related Documentation

- [System Architecture](../core-concepts/architecture.md) - Understanding the layer structure
- [Troubleshooting Guide](../troubleshooting/index.md) - Common issues and solutions
- [Fumadocs Drift Audit Workflow](../../.windsurf/workflows/fumadocs-drift-audit.md) - Detailed audit workflow
- [Drift Assessor Agent](../../.windsurf/agents/drift-assessor/AGENT.md) - Agent configuration

## Questions?

- **Drift detection not working?** Check CI workflow logs for specific errors
- **Need help with Fumadocs audit?** See the detailed workflow documentation
- **Want to add new drift checks?** Propose changes via issue or PR
