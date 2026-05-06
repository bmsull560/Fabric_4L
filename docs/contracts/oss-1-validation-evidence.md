# OSS-1 Cache Adapter Validation Evidence

**Author:** Manus AI  
**Date:** 2026-05-05  
**Scope:** Layer 3 non-default `aiocache` `CachePort` pilot, provider factory, shadow comparator scaffolding, parity tests, and validation evidence.

## Summary

OSS-1 introduced an **opt-in `aiocache`-backed cache adapter** for Layer 3 while preserving the existing legacy Redis-backed cache path as the default. The sprint implemented the adapter behind the `CachePort` seam created in OSS-0, added a small provider factory that requires explicit `aiocache` selection, and added a shadow comparator utility for tests or staging pilots where primary legacy behavior can be compared against an OSS implementation before promotion.

The implementation intentionally does **not** promote `aiocache` to the runtime default. This keeps OSS-1 as a reversible pilot: existing callers can continue to use the legacy adapter, while tests and staging experiments can opt into `AiocacheCacheAdapter` through the shared port contract.

| Area | OSS-1 Outcome | Runtime Default Changed |
|---|---|---:|
| Layer 3 cache adapter | Added `AiocacheCacheAdapter` implementing the existing `CachePort` contract. | No |
| Provider selection | Added `build_cache_port` with legacy as the default and `aiocache` requiring explicit opt-in. | No |
| Shadow validation | Added `ShadowCacheComparator` to compare legacy primary behavior against an opt-in secondary cache port. | No |
| Test coverage | Added shared parity tests that run the same behavior checks against the legacy and `aiocache` adapters. | No |
| Dependency declaration | Added `aiocache>=0.12.3` to the Layer 3 service dependencies. | No |

## Files Changed

| File | Purpose |
|---|---|
| `services/layer3-knowledge/pyproject.toml` | Declares the `aiocache>=0.12.3` dependency required for the non-default OSS adapter. |
| `services/layer3-knowledge/src/cache/aiocache_adapter.py` | Implements the opt-in `AiocacheCacheAdapter` behind the `CachePort` contract. |
| `services/layer3-knowledge/src/cache/factory.py` | Adds a provider factory that preserves legacy as the default and requires explicit `aiocache` selection. |
| `services/layer3-knowledge/src/cache/shadow.py` | Adds optional shadow-comparison scaffolding for primary versus secondary cache-port behavior. |
| `services/layer3-knowledge/src/cache/__init__.py` | Exports OSS-1 cache symbols without removing existing cache exports. |
| `services/layer3-knowledge/tests/test_cache_oss1_parity.py` | Adds parity and shadow tests for the legacy and `aiocache` cache-port implementations. |
| `docs/contracts/oss-1-validation-evidence.md` | Records OSS-1 implementation evidence, validation commands, and promotion guidance. |

## Behavior Covered by OSS-1 Parity Tests

The OSS-1 parity tests verify observable cache-port behavior rather than implementation internals. This allows the legacy adapter and `aiocache` adapter to be compared through the same contract and provides a reusable gate for future cache-provider pilots.

| Behavior | Evidence Added |
|---|---|
| JSON round trip | Both adapters store and retrieve JSON-like dictionaries through `set` and `get`. |
| Hit and miss accounting | Both adapters expose cache statistics after cache hits and misses without coupling tests to a specific stats object shape. |
| Delete, exists, clear-pattern | Both adapters support existence checks, key deletion, pattern-based cleanup, and key cleanup after tests. |
| Increment semantics | Both adapters increment integer values through one logical cache-port operation and return the incremented result. |
| TTL cap behavior | Both adapters enforce the configured maximum TTL rather than blindly accepting a longer requested TTL. |
| Tenant key prefixing | Both adapters preserve tenant-aware key namespacing via the existing `tenant_id` contract. |
| Serializer safety | Both adapters reject pickle serializer configuration and preserve the project’s non-pickle cache-safety boundary. |
| Default preservation | The provider factory keeps the legacy adapter as the implicit default and requires explicit `aiocache` opt-in. |
| Shadow comparison | The shadow comparator reports no mismatches when primary and secondary cache ports produce equivalent behavior. |

## Validation Results

The focused OSS-1 validation gates passed. The full Layer 3 suite and a broad non-API subset were also attempted; those broader runs exposed existing unrelated repository validation blockers outside the OSS-1 cache scope. The OSS-1 focused suite and compile gate should be considered the merge gate for this cache-adapter sprint, while the broader blockers should be tracked separately before adopting an “all Layer 3 tests must pass” policy for future OSS promotion.

| Gate | Command | Result |
|---|---|---|
| Focused OSS-1 cache validation | `PYTHONPATH=src python -m pytest tests/test_cache_oss1_parity.py tests/test_cache_ports.py tests/test_cache_characterization.py -v` from `services/layer3-knowledge` | Passed: `18 passed in 2.80s` |
| Python compile check | `python3.11 -m py_compile services/layer3-knowledge/src/cache/aiocache_adapter.py services/layer3-knowledge/src/cache/factory.py services/layer3-knowledge/src/cache/shadow.py services/layer3-knowledge/src/cache/__init__.py services/layer3-knowledge/tests/test_cache_oss1_parity.py` from repository root | Passed: no compile errors |
| Full Layer 3 suite attempt | `PYTHONPATH=src python -m pytest tests -v` from `services/layer3-knowledge` | Blocked at collection: 386 collected with 6 collection errors in unrelated API/e2e tests. |
| Broad non-blocked Layer 3 attempt with test env | `ENVIRONMENT=test APP_ENV=test TESTING=true PYTHONPATH=src python -m pytest ... -v` over selected non-e2e files | Not used as OSS-1 gate: one API endpoint test stalled and was killed; a narrower non-API run later reported existing failures unrelated to cache adapter changes. |

## Broader Validation Blockers Observed

The broader validation attempts surfaced pre-existing or out-of-scope failures that should be addressed separately. These blockers do not change the OSS-1 runtime default and were not introduced by the cache adapter files.

| Blocker | Observed Evidence | Suggested Follow-Up |
|---|---|---|
| API app circular import during collection | `ImportError: cannot import name '_app_metrics' from partially initialized module ... app_monolith` in `test_e2e_pipeline.py`, `test_exception_handlers.py`, `test_tenant_context_extraction.py`, and `test_versioning_registration.py`. | Move or lazy-load app metric globals and route imports so app modules can be imported during collection without cycles. |
| Optional Neo4j testcontainer typing issue | `NameError: name 'Neo4jContainer' is not defined` in `test_neo4j_schema_integration.py` and `test_vector_e2e.py`. | Add postponed annotation evaluation or skip decorators when optional testcontainer dependencies are unavailable. |
| Production-like rate limiter configuration in tests | Broad selected run without test environment failed with `RateLimiterConfigurationError` for environment `prod`. | Ensure test commands set `ENVIRONMENT=test APP_ENV=test TESTING=true`, or make test fixtures enforce test-safe defaults before app middleware construction. |
| Legacy broad unit failures | Narrower non-API run reported existing failures in pack-loader cache expectations, typed-dict validation shape, hybrid-search result constructor shape, async iterator mocks, and value-pack async context manager mocks. | Track as separate Layer 3 test-harness and domain-test cleanup before using that broad suite as a promotion gate. |

## Rollout and Rollback Guidance

OSS-1 should remain a **non-default pilot** until staging evidence shows parity under realistic traffic. The safest rollout sequence is to use the provider factory to keep legacy behavior in production, instantiate the `aiocache` adapter only in targeted tests or staging, and run the shadow comparator against representative cache operations before any default switch.

| Stage | Recommendation | Exit Criteria |
|---|---|---|
| Local validation | Continue running focused parity and characterization tests before cache-related commits. | OSS-1 focused suite passes with no adapter-specific skips. |
| Staging shadow pilot | Run legacy as primary and `aiocache` as secondary through `ShadowCacheComparator` for representative operations. | No correctness mismatches for reads, writes, deletes, increments, TTL behavior, and tenant key isolation. |
| Observability review | Compare hit rate, miss rate, latency, exception rate, and key cardinality between providers. | OSS metrics are equal or better, and no tenant isolation anomalies are observed. |
| Promotion decision | Only consider changing defaults after broader Layer 3 validation blockers are resolved. | Full agreed cache and Layer 3 promotion gate passes under a stable test environment. |
| Rollback | Keep provider selection set to legacy if any parity, latency, or tenant-isolation regression appears. | Reverting the provider selection restores legacy behavior without data migration. |

## OSS-2 Recommendation

The next recommended sprint should not promote `aiocache` by default yet. Instead, OSS-2 should either complete a staging shadow pilot for this cache adapter or address the broader Layer 3 validation blockers so future OSS pilots can use a stronger full-suite gate. If the team wants to continue OSS substitution work immediately, the most valuable OSS-2 target is **cache shadow telemetry and rollout controls**: add explicit configuration, sampling, mismatch logging, and dashboards around the existing shadow comparator while retaining the legacy default.
