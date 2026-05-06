# Project Instructions for Gemini CLI

## Project Context

This repository should be treated as production-grade software.

Before editing:

- Read the relevant files.
- Identify existing conventions.
- Search for tests.
- Prefer compatibility-preserving changes.
- Avoid broad rewrites.

## Architecture Rules

- Respect existing module boundaries.
- Do not introduce new dependencies without justification.
- Do not edit generated files manually.
- Do not return fake production data.
- Do not add hardcoded secrets.
- Do not create no-op security or safety implementations.
- Fail closed for security, tenant isolation, money, workflow, and governance paths.

## Frontend Rules

- React components should consume domain/view models, not raw API DTOs.
- Keep DTO-to-domain mapping in adapters.
- Validate network responses before using them.
- Avoid `any`.

## Backend Rules

- FastAPI routes should use explicit request/response models.
- Pydantic DTOs define API contracts.
- Use clear HTTP errors instead of silent fallback behavior.
- Preserve trace IDs, tenant IDs, and audit metadata.

## Execution Style

For each task:

1. Inspect.
2. Plan briefly.
3. Patch narrowly.
4. Test.
5. Report changed files, validation run, and remaining risks.
