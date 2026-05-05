# SDK and CLI Production-Readiness Plan

Fabric_4L already includes OpenAPI contracts, SDK generation scripts, Python SDK scaffolding, and SDK publication workflows. This plan closes the readiness gap by defining the release contract that must hold before SDK and CLI support is presented as production-ready.

## Release Contract

| Area | Required repository foundation | Production-ready evidence |
|---|---|---|
| OpenAPI source of truth | Versioned contracts under `contracts/openapi/` and drift-check workflows. | CI proves generated SDK clients match the latest service contracts. |
| Python SDK | `sdk/python` package with auth and CLI modules. | Package builds reproducibly, installs in a clean environment, and calls live staging APIs. |
| CLI | `valuefabric` command surface for auth, health, workflow, and evidence operations. | CLI smoke test authenticates against staging and performs at least one read-only API call. |
| Versioning | Semantic package version and changelog discipline. | Release tags map to immutable package artifacts. |
| Security | Token input via environment variables or secure storage only. | No token or secret appears in logs, command history, generated fixtures, or evidence artifacts. |

## Minimum Production CLI Commands

The first production CLI surface should stay intentionally small. It should include `valuefabric auth status`, `valuefabric health`, `valuefabric workflows list`, `valuefabric evidence validate`, and `valuefabric openapi export`. Write operations should remain opt-in behind explicit confirmation flags until RBAC and audit evidence are complete.

## Acceptance Evidence

SDK and CLI readiness must be demonstrated by a clean package build, a clean install into a temporary virtual environment, a read-only staging API smoke test, and CI evidence that OpenAPI drift did not occur. Documentation-only evidence is not sufficient for production PASS.
