# Layer 3 Strict Builder Enforcement Implementation Plan

**Author:** Manus AI  
**Repository:** `bmsull560/Fabric_4L`  
**Scope:** Layer 3 Neo4j tenant-isolation hardening  
**Status:** Proposed implementation plan

## Executive summary

Layer 3 currently has a launch-blocking tenant-isolation risk because multiple Neo4j query paths still issue raw Cypher through `session.run(...)`, `tx.run(...)`, or helper wrappers without a uniform construction and validation contract. Some queries already include `tenant_id` filters, but the enforcement model is inconsistent, and modules such as `services/layer3-knowledge/src/analytics/centrality.py` include broad graph reads such as `MATCH (n)` that can cross tenant boundaries when executed against Neo4j Community Edition.

The recommended solution is **Strict Builder Enforcement**. Tenant-owned graph operations should be constructed through a required tenant-scoped builder or an approved query object, while raw Cypher should be prohibited in tenant-facing Layer 3 code unless it is explicitly classified as a system-scope operation. This plan avoids automatic query rewriting because mutation middleware is difficult to make safe for complex Cypher involving aliases, `OPTIONAL MATCH`, subqueries, `CALL { ... }`, GDS procedures, APOC calls, and graph projections.

> **Target state:** Layer 3 services can only execute Neo4j queries through tenant-aware query builders, reviewed system-scope query wrappers, or guarded low-level execution seams. CI fails when tenant-owned code introduces unapproved raw Cypher or an unscoped graph access pattern.

## Current implementation baseline

The repository already contains several useful building blocks. `TenantScopedCypher` exists in `packages/shared/src/value_fabric/shared/identity/isolation.py` and can currently build tenant-filtered node and relationship reads plus tenant-injected node creates. Layer 3 also contains `services/layer3-knowledge/src/security/query_validator.py`, which provides `QueryValidator` and `ValidatedNeo4jSession` for detecting some unsafe `Entity` matches and unsafe delete patterns. These are good foundations, but they are not yet sufficient as an enterprise-wide enforcement mechanism because the current validator is label-specific, regex-oriented, and not uniformly applied to Layer 3 execution paths.

| Existing asset | Current value | Required evolution |
|---|---|---|
| `TenantScopedCypher` | Provides basic tenant-filtered `MATCH`, `CREATE`, and relationship matching helpers. | Expand into a broader Layer 3 graph-query DSL that supports the actual query shapes used by analytics, retrieval, ingestion, routes, and services. |
| `QueryValidator` | Detects a subset of unscoped `Entity` queries and unsafe deletes. | Broaden into a CI/test guard that covers tenant-owned labels, relationship endpoint scoping, raw Cypher allowlists, and system-scope exceptions. |
| `ValidatedNeo4jSession` | Demonstrates defensive runtime validation around `session.run`. | Convert into a non-rewriting guard for tests/staging and an approved low-level execution seam, not a primary query authoring mechanism. |
| Layer 3 test stabilization work | Improved broader validation readiness and API collection health. | Add tenant-isolation suites as mandatory gates before future OSS rollout work. |

## Enforcement principles

Strict Builder Enforcement should follow a **fail-closed** security model. A query should be considered unsafe unless it is constructed by an approved tenant-scoped builder, executed through an approved system-scope escape hatch, or explicitly validated as tenant-scoped by tests. This is especially important for Neo4j Community Edition deployments because tenant isolation must be enforced in the application layer.

| Principle | Implementation implication |
|---|---|
| **Tenant context is mandatory** | Every tenant-owned Layer 3 service method that touches Neo4j must receive or resolve a tenant context before constructing the query. |
| **Builders are canonical** | Tenant-scoped query construction should happen through `TenantScopedCypher` or successor builder classes, not inline raw strings. |
| **Raw Cypher is exceptional** | Inline Cypher in tenant-facing code should fail static checks unless wrapped in an approved `SystemCypher` or `ScopedCypher` object. |
| **Relationship safety requires both endpoints** | Relationship reads/writes must scope all tenant-owned endpoint nodes, not just one side. |
| **Optional matches must remain scoped** | `OPTIONAL MATCH` clauses that touch tenant-owned nodes must include tenant filters in the pattern or immediately adjacent `WHERE` clause. |
| **System operations are explicit** | Schema initialization, health checks, migrations, backups, and GDS graph management require visible system-scope declarations and review. |
| **No silent query rewriting** | Runtime guardrails may reject, log, or shadow-check unsafe queries, but should not mutate Cypher semantics automatically. |

## Proposed architecture

The target architecture should introduce a small, explicit graph-query layer under a shared or Layer 3 package path. The preferred location is `packages/shared/src/value_fabric/shared/identity/cypher.py` if multiple services will consume it, or `services/layer3-knowledge/src/db/scoped_cypher.py` if it remains Layer 3-specific. Given the current repository already hosts `TenantScopedCypher` in shared identity utilities, the pragmatic path is to expand that shared module first and later split it if it becomes too large.

| Component | Responsibility | Notes |
|---|---|---|
| `TenantScopedCypher` | Build tenant-safe Cypher fragments and complete query objects. | Extend beyond simple `match_node`, `create_node`, and `match_relationship`. |
| `ScopedQuery` dataclass | Carry `cypher`, `params`, `scope`, `labels`, and `operation` metadata. | Lets execution guards distinguish tenant-scope, system-scope, migration, health, and backup operations. |
| `TenantLabelPolicy` | Maintain the set of tenant-owned labels and allowed global labels. | Prevents validators from checking only `Entity` while missing `Formula`, `ValuePack`, `Capability`, `Product`, etc. |
| `ScopedNeo4jSession` | Execute only `ScopedQuery` objects by default. | Provides `run_scoped(query)` and limits `run_raw(...)` to audited system-scope operations. |
| `SystemCypher` escape hatch | Represent schema, health, migration, and backup queries that legitimately operate globally. | Requires reason, owner, ticket/doc reference, and test coverage. |
| Static enforcement tests | Scan Layer 3 source for raw `session.run`, `tx.run`, `MATCH`, `MERGE`, `CREATE`, `DELETE`, `CALL db`, and `CALL gds` patterns. | CI should fail on new violations unless allowlisted. |
| Runtime guard | In tests and staging, reject unapproved raw Cypher and report metadata. | Should validate and block, not rewrite. |

The execution API should make safe usage the path of least resistance. A service should call a query builder, receive a `ScopedQuery`, and pass it to a scoped session. Legacy direct usage should be fenced behind compatibility shims and removed incrementally.

```python
query = TenantScopedCypher(tenant_id).match_node(
    alias="p",
    label="Product",
    extra_where="p.status = $status",
    extra_params={"status": "active"},
    return_clause="p {.id, .name, .category} AS product",
)
result = await scoped_session.run_scoped(query)
```

For complex queries, the builder should support composable fragments rather than forcing every query through one monolithic method. The important invariant is that every tenant-owned node pattern and every relationship endpoint is scoped before execution.

## Builder feature backlog

The current builder is too small for the query variety in Layer 3. The first implementation sprint should expand builder coverage around the patterns that appear most frequently in the repository scan.

| Builder capability | Required query support | Priority |
|---|---|---|
| Tenant-scoped node match | `MATCH (alias:Label {id: $id, tenant_id: $tenant_id})`, `MATCH (alias:Label) WHERE alias.tenant_id = $tenant_id AND ...` | P0 |
| Tenant-scoped optional match | `OPTIONAL MATCH` with tenant-scoped endpoint filters. | P0 |
| Tenant-scoped relationship match | Both source and target nodes must be tenant-filtered. | P0 |
| Tenant-scoped merge/create | Inject `tenant_id` into created node properties and verify related endpoints. | P0 |
| Tenant-scoped update/delete | Require scoped match before `SET`, `DELETE`, or `DETACH DELETE`. | P0 |
| Paginated list queries | Count/data query pairs with shared tenant predicates. | P1 |
| Full-text and vector index wrappers | Allow `CALL db.index.fulltext.queryNodes` and vector search only when yielded nodes are tenant-filtered before return. | P1 |
| GDS projection wrappers | Project tenant-filtered subgraphs only; system-scope GDS version checks remain explicitly global. | P1 |
| Bulk ingestion helpers | `UNWIND`-based `MERGE` and relationship loading with tenant propagated from records or execution context. | P1 |
| Governance/versioning helpers | Formula, variable, benchmark, and value-pack workflows with `tenant_id` or `tenantId` normalization. | P2 |
| System-scope wrapper | Health, schema, index, constraint, migration, and backup metadata queries. | P2 |

## Migration inventory and prioritization

The repository scan found raw Cypher patterns across analytics, retrieval, API routes, ingestion, services, agents, backup, schema, and migration modules. Not every raw query is equally risky. The migration should start with high-risk tenant-facing reads that can expose cross-tenant graph data, then move to writes and finally to explicitly global operational code.

| Priority | Area | Representative modules | Risk rationale | Target outcome |
|---|---|---|---|---|
| P0 | Analytics graph-wide reads | `analytics/centrality.py`, `analytics/communities.py`, `analytics/similarity.py` | Contains broad `MATCH (n)` and graph algorithms that can aggregate across tenants. | All analytics queries require `tenant_id` and project tenant-scoped subgraphs. |
| P0 | Retrieval and GraphRAG | `retrieval/graph_rag.py`, `retrieval/hybrid_search.py`, `retrieval/vector_store.py` | Search and RAG are user-facing and can leak nodes through index results if post-filtering is absent. | Full-text/vector outputs are filtered by tenant before scoring and returning. |
| P0 | API entity/value tree routes | `api/routes/entities.py`, `api/app_monolith.py`, `api/routes/value_trees.py` | Public endpoints query graph entities and relationships. | Endpoints use scoped query helpers or `db/tenant_queries.py` exclusively. |
| P1 | Value packs, formulas, variables, benchmarks, models | `api/routes/value_packs.py`, `api/routes/formulas.py`, `api/routes/formula_governance.py`, `api/routes/variables.py`, `api/routes/benchmarks.py`, `api/routes/models.py` | Business objects are tenant-owned; inconsistent `tenant_id` versus `tenantId` semantics create bypass risk. | Normalize tenant property policy and migrate routes to builders. |
| P1 | Domain services | `services/product_service.py`, `case_study_service.py`, `competitive_intel_service.py`, `roi_calculator_service.py`, `evidence_search.py`, `signal_*` | Service layer contains many mostly scoped raw queries but lacks enforced construction. | Replace inline Cypher with service-specific query factories backed by the builder. |
| P1 | Ingestion loaders and sync | `ingestion/neo4j_loader.py`, `ingestion/sync_manager.py` | Bulk writes can create unscoped records or metadata. | Tenant context is mandatory for all tenant data loads; sync metadata either tenant-scoped or classified as system metadata. |
| P2 | Agents and provenance | `agents/provenance_tracking.py`, `roi_calculation.py`, `value_tree_projection.py`, `whitespace_analysis.py` | Agent workflows can create/read provenance and derived intelligence across graph layers. | Agent graph operations use builders and scoped provenance helpers. |
| P2 | Backup, schema, migrations, health | `backup/backup_manager.py`, `schema/initializer.py`, `migrations/*.py`, `db/driver.py` | Some global access is legitimate but must be explicit. | Wrap in `SystemCypher` with documented reasons and restricted call sites. |

## Implementation phases

### Phase 1: Establish policy and query metadata

The first phase should define the policy model before refactoring high-risk queries. This includes a tenant-owned label registry, global-operation categories, and a query object format. The team should also decide how to handle both `tenant_id` and `tenantId`, because the repository currently contains both naming conventions in formula and variable routes.

| Deliverable | Acceptance criteria |
|---|---|
| `TenantLabelPolicy` | Includes all tenant-owned labels used by Layer 3, such as `Entity`, `Product`, `Evidence`, `Formula`, `Variable`, `ValuePack`, `Capability`, `PainSignal`, `ValueDriver`, `UseCase`, `Persona`, `Competitor`, `Battlecard`, `ROITemplate`, `ROICalculation`, `BenchmarkDataset`, and `ValueModel`. |
| `ScopedQuery` model | Represents tenant, system, migration, health, backup, and schema scopes with metadata. |
| `SystemCypher` escape hatch | Requires `reason`, `owner`, `operation`, and `allowlist_key`. |
| Tenant property policy | Documents whether each label uses `tenant_id`, `tenantId`, or a compatibility alias during migration. |

### Phase 2: Expand the builder and execution seam

The second phase should make safe query construction ergonomic enough that service refactors are straightforward. This means adding common methods for optional matches, relationship writes, deletes, list pagination, bulk `UNWIND`, and post-filtered procedure calls.

| Deliverable | Acceptance criteria |
|---|---|
| Expanded `TenantScopedCypher` | Supports node match, optional match, relationship match, create, merge, update, delete, list pagination, and relationship endpoint scoping. |
| `ScopedNeo4jSession` | Default execution accepts `ScopedQuery`; raw execution requires `SystemCypher` or a named allowlist entry. |
| Builder unit tests | Verify every builder method injects tenant predicates and preserves provided parameters. |
| Validator compatibility | `QueryValidator` can validate generated queries and reject representative unsafe queries across all tenant-owned labels. |

### Phase 3: Add static and runtime gates before broad refactor

Before touching every service, add guardrails in warn-only mode. This creates visibility into current violations and prevents new unscoped queries from being introduced during migration.

| Gate | Initial mode | Final mode |
|---|---|---|
| Static raw Cypher scan | Report existing violations into a baseline file. | Fail on any new unapproved `session.run`, `tx.run`, `MATCH`, `MERGE`, `CREATE`, `DELETE`, or GDS/API procedure call in tenant-facing paths. |
| Runtime `ValidatedNeo4jSession` guard | Enabled in tests for selected modules. | Enabled by default in Layer 3 tests and staging, with production opt-in after burn-in. |
| Tenant isolation fixture | Provides tenant A and tenant B graph data. | Required for every migrated module’s test suite. |
| Allowlist review | Allows current system/migration exceptions. | Requires a reason and owner for each exception. |

### Phase 4: Migrate P0 high-risk modules

The fourth phase should eliminate the highest-risk cross-tenant read paths. These are the routes and services most likely to return graph data to users or aggregate graph-wide insights.

| Workstream | Implementation details | Tests |
|---|---|---|
| Analytics centrality | Replace `MATCH (n)` fallback queries with tenant-filtered node queries; require tenant-scoped GDS projections. | Tenant A/B centrality test proves no cross-tenant nodes affect score or output. |
| Analytics communities | Scope value-driver subgraphs, community projections, and modularity reads by tenant. | Community output excludes tenant B nodes even when labels and relationship types overlap. |
| Analytics similarity | Scope source, candidate, common-neighbor, shortest-path, and explanation lookups. | Similarity result never includes cross-tenant candidate or shared neighbor. |
| GraphRAG retrieval | Scope full-text/vector search yields before expansion; scope entity batch hydration and hop expansion. | Query with same entity IDs across tenants returns only current tenant results. |
| API entity routes | Replace raw entity list/detail/relationship queries with shared `db/tenant_queries.py` or builder-backed query factories. | Endpoint tests cover list, detail, relationships, provenance, and graph visualization isolation. |

### Phase 5: Migrate P1 business routes and domain services

After the highest-risk reads are safe, migrate routes and services that create or mutate tenant-owned graph objects. This phase should also normalize tenant property naming.

| Workstream | Implementation details | Tests |
|---|---|---|
| Value packs | Scope pack CRUD, formula retrieval, execution records, fork/copy operations, and seeded industry packs. | Pack execution and fork tests prove related formulas/drivers/benchmarks are same-tenant. |
| Formulas and governance | Add tenant filters to governance/versioning/dependency queries; resolve `tenantId` compatibility. | Formula dependency tests prove incoming and outgoing dependencies are tenant-local. |
| Variables and benchmarks | Scope list/get/create/update/stats/source-binding queries. | Registry stats exclude tenant B variables and bindings. |
| Models | Scope `ValueModel` list/detail/create/update/delete and relationship queries. | Model ownership and delete tests prove tenant boundaries. |
| Product/evidence/competitive/ROI services | Move inline Cypher into builder-backed query factories while preserving existing method contracts. | Existing DIL tests plus new tenant A/B isolation tests pass. |
| Ingestion | Require tenant context for entity and relationship bulk loads; reject records missing tenant. | Bulk ingestion rejects missing tenant and cannot link cross-tenant endpoints. |

### Phase 6: Classify and wrap P2 operational/global code

Some modules legitimately need global visibility. Schema initialization, migrations, backups, health checks, and constraint/index introspection cannot always be tenant-scoped. These paths should be auditable rather than forced through tenant builders.

| Module category | Treatment | Required controls |
|---|---|---|
| Health checks | Use `SystemCypher.health_check("RETURN 1 AS check")`. | Only allows constant-return and metadata checks. |
| Schema/index initialization | Use `SystemCypher.schema_operation(...)`. | Restricted to `SHOW`, `CREATE CONSTRAINT`, `CREATE INDEX`, `DROP INDEX`, and approved migration statements. |
| Tenant migration scripts | Use `SystemCypher.migration(...)`. | Requires dry-run counts, backup note, and explicit default tenant handling. |
| Backup/restore | Separate tenant-scoped backup from administrative global backup. | Global backup requires admin mode and should not be callable from tenant-facing API paths. |
| GDS graph management | Version checks and graph drops can be system-scope; projections and algorithms over tenant data must be tenant-scoped. | Projection names should include tenant-safe identifiers or hashes. |

### Phase 7: Enforce CI as a release gate

Once P0 and P1 modules are migrated, the static scan should move from warn-only to fail-closed mode. The allowlist should shrink to only operational/system files.

| CI gate | Command concept | Pass condition |
|---|---|---|
| Static tenant-scope scan | `python scripts/check_layer3_cypher_scope.py services/layer3-knowledge/src` | No unapproved raw Cypher in tenant-facing modules. |
| Builder unit tests | `pytest tests/test_tenant_scoped_cypher.py` | All builder methods produce expected tenant filters. |
| Runtime guard tests | `pytest tests/test_neo4j_query_guard.py` | Unsafe raw queries raise `UnscopedQueryError`; system-scope escape hatches require metadata. |
| Tenant A/B isolation tests | `pytest tests/test_layer3_tenant_isolation_*.py` | No endpoint, service, retrieval, analytics, or ingestion test returns cross-tenant data. |
| Broad Layer 3 validation | Existing broader Layer 3 suite | No regressions from builder migration. |

## Test strategy

Testing should combine static analysis, unit tests for query construction, runtime guard tests, and integration-style tenant A/B fixtures. Static checks alone are not enough because a query can include the string `tenant_id` while still failing to scope all relevant aliases. Runtime checks alone are not enough because not every path is executed in every test run.

| Test type | Purpose | Example assertion |
|---|---|---|
| Builder snapshot tests | Confirm generated Cypher and parameters are stable. | `TenantScopedCypher.match_relationship(...)` filters both `from_alias.tenant_id` and `to_alias.tenant_id`. |
| Negative validator tests | Confirm unsafe Cypher fails closed. | `MATCH (n) RETURN n` is rejected in tenant-facing context. |
| Static source tests | Prevent new raw Cypher from entering tenant code. | New `session.run("MATCH ...")` in `src/retrieval` fails CI unless builder-backed. |
| Tenant A/B data tests | Prove behavior, not just syntax. | A query for tenant A cannot return tenant B nodes with the same `id`, `name`, or label. |
| System-scope tests | Ensure legitimate global operations are explicit. | `SHOW INDEXES` is allowed only through `SystemCypher.schema_operation`. |
| Regression tests | Preserve existing API/service behavior. | Existing GraphRAG, DIL, product, ROI, and value-pack tests continue to pass. |

## Static scan design

A practical static scanner should start simple and become stricter over time. It should parse Python files with `ast`, identify string literals passed to methods named `run`, `execute_query`, or project-specific wrappers, and flag raw Cypher keywords when they appear in tenant-facing paths. Regex-only scanning can be used as a first pass, but AST inspection avoids many false positives from comments and docstrings.

| Scanner rule | Severity | Notes |
|---|---|---|
| `session.run(...)` or `tx.run(...)` with string literal Cypher in tenant-facing paths | Error after baseline migration | Must be replaced by `run_scoped(ScopedQuery)`. |
| `execute_query(...)` with raw Cypher | Error after baseline migration | Same treatment as `session.run`. |
| Cypher keyword string assigned to variable and later passed to run | Error | Track simple variable assignment flows. |
| `MATCH (n)` or `MATCH ()-[r]->()` in tenant-facing path | Error | Usually unbounded graph read. |
| `OPTIONAL MATCH` touching tenant-owned labels without alias tenant predicate | Error | Must scope optional endpoint or adjacent `WHERE`. |
| `CALL db.index.fulltext.queryNodes` without tenant post-filter | Error | Full-text indexes can return cross-tenant nodes if not filtered. |
| `CALL gds.*` tenant data operation without tenant-scoped projection | Error | GDS algorithms should operate on tenant-filtered projections. |
| `SHOW INDEXES`, `SHOW CONSTRAINTS`, `RETURN 1`, `CALL dbms.components` | Allowed only in system-scope modules | Requires explicit allowlist. |

## Runtime guard behavior

The runtime guard should be conservative. It should reject unsafe queries in test and staging, log structured findings, and optionally run in production in observe-only mode before promotion to fail-closed. It should not attempt to rewrite queries.

| Environment | Recommended mode | Behavior |
|---|---|---|
| Unit tests | Fail-closed | Any unapproved raw or unscoped query fails immediately. |
| Integration tests | Fail-closed for tenant-facing paths; allowlisted for migrations/schema. | Catches real driver usage. |
| Development | Fail-closed by default with override for migration scripts. | Gives developers fast feedback. |
| Staging | Fail-closed for APIs and services; warn-only for approved operational tasks during initial rollout. | Validates launch readiness. |
| Production | Start warn-only for one release, then fail-closed for tenant-facing paths. | Reduces rollout risk while measuring false positives. |

## Acceptance criteria for completion

Strict Builder Enforcement should be considered complete only when the codebase and CI enforce the contract rather than merely documenting it.

| Acceptance criterion | Verification method |
|---|---|
| No P0 tenant-facing module contains unapproved raw Cypher execution. | Static scanner passes without P0 exceptions. |
| All P0 analytics and retrieval queries are tenant-scoped by construction. | Builder tests and tenant A/B integration tests pass. |
| All public API graph endpoints use builders or shared tenant query helpers. | Static scanner plus endpoint isolation tests. |
| All tenant-owned relationship queries scope both endpoints. | Negative tests with cross-tenant same-ID data. |
| All raw global operations are wrapped in `SystemCypher` with reason metadata. | Allowlist file review and scanner pass. |
| CI fails on newly introduced unscoped Cypher. | Deliberate negative fixture test in scanner suite. |
| Runtime guard blocks unsafe tenant-facing raw queries in tests. | `UnscopedQueryError` tests pass. |
| Documentation explains builder usage and escape-hatch policy. | Developer docs merged with examples. |

## Suggested sprint breakdown

This should be implemented as a sequence of focused sprints rather than one large refactor. The first sprint creates the enforcement infrastructure and makes current violations visible. The next two sprints eliminate the highest-risk read paths. Later sprints handle long-tail service and operational code.

| Sprint | Theme | Main deliverables | Exit criteria |
|---|---|---|---|
| TSE-0 | Enforcement foundation | `ScopedQuery`, expanded policy registry, baseline scanner, initial docs. | Scanner reports current baseline without failing CI. |
| TSE-1 | Builder expansion | P0 builder methods, runtime guard integration, builder tests. | Unsafe representative queries fail; safe builder queries pass. |
| TSE-2 | Analytics and retrieval migration | Centrality, communities, similarity, GraphRAG, hybrid search, vector store. | Tenant A/B analytics and retrieval tests pass. |
| TSE-3 | API endpoint migration | Entity, value tree, app monolith graph routes, high-risk public endpoints. | Endpoint isolation tests pass; no raw P0 API Cypher remains. |
| TSE-4 | Business route migration | Value packs, formulas, variables, benchmarks, models. | P1 route scanner clean; tenant property policy implemented. |
| TSE-5 | Service and ingestion migration | Product, evidence, competitive, ROI, signal, ingestion, sync. | DIL and ingestion tests pass with tenant A/B isolation. |
| TSE-6 | Operational classification | Schema, migration, backup, health, GDS system wrappers. | Only reviewed `SystemCypher` allowlist remains. |
| TSE-7 | CI fail-closed | Static scanner fail-closed, runtime guard default in tests/staging. | Broad Layer 3 suite and tenant isolation gates pass. |

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Builder API becomes too generic or too complex. | Developers bypass it and return to raw Cypher. | Provide domain-specific query factories for repeated patterns and keep builder primitives composable. |
| False positives in static scanner block legitimate work. | CI friction slows migration. | Use a baseline file during TSE-0/TSE-1 and require metadata for exceptions. |
| GDS and full-text query patterns are hard to scope. | Analytics/retrieval remains risky. | Create specialized builder methods for GDS projections and index post-filtering rather than ad hoc raw queries. |
| `tenant_id` versus `tenantId` mismatch creates gaps. | Some labels appear scoped but are not consistently filtered. | Define label-level tenant property policy and migration compatibility rules. |
| Existing tests rely on global data behavior. | Refactor causes broad test churn. | Introduce tenant A/B fixtures and update tests to encode tenant-correct expectations. |
| Operational scripts need global access. | Overly strict enforcement blocks migrations/backups. | Use explicit `SystemCypher` categories with admin-only call sites. |

## Immediate next actions

The most effective next implementation step is **TSE-0**, because it creates the policy and visibility needed to control the rest of the migration. I recommend starting with the following concrete task list.

| Order | Task | Output |
|---|---|---|
| 1 | Add `ScopedQuery`, `SystemCypher`, and `TenantLabelPolicy` near the existing `TenantScopedCypher`. | Shared query metadata foundation. |
| 2 | Expand `TenantScopedCypher` with optional match, merge, update, delete, and relationship-write helpers. | Builder primitives needed by P0 modules. |
| 3 | Create `scripts/check_layer3_cypher_scope.py` with AST-based raw Cypher detection. | Baseline visibility into all violations. |
| 4 | Add `tests/test_tenant_scoped_cypher.py` and `tests/test_layer3_cypher_scope_scanner.py`. | CI-ready proof that enforcement works. |
| 5 | Generate `docs/contracts/layer3-cypher-scope-baseline.md` or JSON allowlist. | Reviewed baseline for phased cleanup. |
| 6 | Migrate `analytics/centrality.py` first. | Removes the confirmed highest-risk `MATCH (n)` path. |

## Recommended definition of done for TSE-0/TSE-1

TSE-0 and TSE-1 should be treated as a security foundation milestone. They are complete when new unscoped raw Cypher cannot enter Layer 3 unnoticed, even if the existing baseline has not yet been fully migrated.

| Requirement | Done when |
|---|---|
| Policy exists | Tenant-owned labels and system-scope categories are codified in code and docs. |
| Builder supports core operations | CRUD, relationship matching, relationship creation, optional matching, and delete helpers are covered by tests. |
| Scanner exists | Current violations are inventoried and new violations can fail in changed files. |
| Runtime guard exists | Unsafe raw tenant-facing query raises in tests. |
| First high-risk module migrated | `analytics/centrality.py` no longer has tenant-facing `MATCH (n)` or unscoped relationship queries. |

## Conclusion

Strict Builder Enforcement should be implemented as an explicit contract: **tenant-owned graph access must be scoped by construction, raw Cypher must be exceptional, and CI must enforce the rule**. The current repository already contains the foundations, but they need to be expanded from isolated helpers into a full query-authoring, execution, and validation framework. The highest-value path is to create the enforcement infrastructure first, migrate analytics and retrieval immediately after, and then progressively close the long tail across API routes, domain services, ingestion, agents, and operational code.
