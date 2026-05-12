# Tests Quick Start: Infra-backed + Default No-Infra Coverage

This repository intentionally supports two complementary test workflows:

1. **Infra-backed suite** for full integration/security confidence.
2. **Default no-infra fallback suite** so core behavioral/contract checks still run when Postgres/Redis/Neo4j are not available.

## 1) Default local loop (no infra required)

Run this first for fast feedback:

```bash
pytest tests/contract/test_no_infra_adapter_contracts.py -q
```

This validates infra-gating contracts using mocks/fakes (startup commands, skip messaging, and probe adapter behavior) without requiring running services.

## 2) Bring up infrastructure for full coverage

Start dependencies:

```bash
docker compose up -d postgres redis neo4j
```

Then run the standard test flow:

```bash
make verify
```

For agent/skill changes, also run:

```bash
make evals
```

## Infra-gated test behavior

When infra is unavailable locally, tests that require those dependencies are skipped with high-visibility reasons that include:

- The exact startup command.
- Affected test categories (what coverage you are losing).

At the end of the run, pytest prints an **infra-gated skip coverage** summary that reports skip counts by dependency:

- Postgres
- Redis
- Neo4j

This makes missing local/CI coverage explicit.

## Suggested daily workflow

1. `pytest tests/contract/test_no_infra_adapter_contracts.py -q`
2. `docker compose up -d postgres redis neo4j`
3. `make verify`
4. (If applicable) `make evals`


## Contract test environment contract (CI vs local)

`tests/contract/conftest.py` enforces service-availability behavior using explicit environment flags:

- `CONTRACT_TEST_MODE=mock` → bypasses live service health checks (explicit mocked path).
- Strict/fail-closed mode is enabled when any of these are truthy: `CI`, `GITHUB_ACTIONS`, `CONTRACT_TEST_ENFORCE`, or `CONTRACT_TEST_STRICT`.
- Local default (none of the strict flags set) remains developer-friendly: missing Layer 3/4/5 services cause contract tests to skip instead of fail.

### Required CI contract-test job settings

For CI jobs that expect live services, set:

```bash
CI=true
CONTRACT_TEST_ENFORCE=1
```

For CI jobs that intentionally run mocked contract tests, set:

```bash
CI=true
CONTRACT_TEST_MODE=mock
```

This keeps mocked behavior explicit and auditable in workflow configuration rather than relying on implicit defaults.
