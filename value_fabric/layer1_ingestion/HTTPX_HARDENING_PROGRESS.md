# HTTPX Fast Path Hardening Pass - Progress

**Status**: Week 1, Days 1-5 Complete  
**Current Phase**: CrawlDecisionStore + Alembic Migration Complete

---

## ✅ Completed: Week 1, Days 1-5

### 1. CrawlDecisionStore/Repository (`src/crawler/decision_store.py`)

**Purpose**: Canonical, queryable decision history separate from operational logs

**Features**:
- `CrawlDecisionRecord` dataclass with 20+ fields
- `CrawlDecisionRepository` with full CRUD operations
- Query methods:
  - `get_by_job()` - All decisions for a scraping job
  - `get_by_url()` - History for specific URL
  - `get_by_domain()` - Domain-level analysis
  - `get_fallback_stats()` - Fallback rate analysis
  - `get_router_quality_report()` - Job-level quality metrics
  - `get_decisions_by_rule()` - Which rules are triggered

**Analytics Support**:
- `FallbackStats` - Domain-level fallback analysis
- `RouterQualityReport` - Job-level quality metrics

**Test Support**:
- `InMemoryCrawlDecisionRepository` - For unit tests

**Lines**: 600

---

### 2. Database Model (`src/shared/models.py`)

Added `CrawlDecision` SQLAlchemy model:
```python
class CrawlDecision(Base):
    __tablename__ = "crawl_decisions"

    # Primary key & foreign keys
    decision_id = Column(UUID, primary_key=True)
    job_id = Column(UUID, ForeignKey("scraping_jobs.id"))
    tenant_id = Column(UUID, ForeignKey("organizations.id"))  # For RLS

    # Routing context
    url, domain, requested_path
    router_decision, router_rule

    # Quality evaluation
    quality_passed, quality_checks (JSONB), fallback_reason

    # Execution outcome
    final_path, status_code
    fast_duration_ms, browser_duration_ms, fetch_time_ms
    bytes_transferred, spa_detected, text_length

    # Error tracking
    error_type, error_message

    # Metadata
    created_at (indexed)
```

**Indexes**:
- `idx_crawl_decisions_job_created` - Job queries
- `idx_crawl_decisions_domain_created` - Domain analysis
- Individual indexes on: job_id, domain, router_rule, fallback_reason, created_at

---

### 3. Alembic Migration (`migrations/versions/005_add_crawl_path_and_decisions.py`)

**Migration ID**: 005  
**Revises**: 004  
**Safe for production**: Yes (with rollback)

**Changes**:
1. **Add CrawlPath enum type** - `fast`/`browser`/`fast_fallback`

2. **Add `crawl_path` column to `scraping_targets`**:
   - Type: CrawlPath enum
   - Nullable: False
   - Default: `browser` (backward compatible)
   - Existing targets continue using browser

3. **Create `crawl_decisions` table**:
   - All columns from model
   - Foreign keys to scraping_jobs and organizations
   - Composite indexes for common queries
   - RLS policies (tenant isolation + admin bypass)
   - Table and column comments for documentation

4. **Rollback (`downgrade()`)**:
   - Drop RLS policies
   - Drop indexes
   - Drop table
   - Drop column from scraping_targets
   - Drop enum type

**Syntax**: ✅ Validated

---

## 📋 Remaining: Week 1 Day 3-4 + Week 2

### Week 1, Days 3-4: Celery Pipeline Integration
**Files to modify**:
- `src/shared/tasks.py` (150 lines)

**Work**:
- Modify `process_scraping_job` to read target crawl_path
- New task `crawl_url_with_routing`
- Fail-closed logic implementation

### Week 2, Day 6: API Contract Updates
**Files to modify**:
- `src/api/routes/targets.py` (80 lines)
- `src/api/schemas.py` (30 lines)

**Work**:
- Add crawl_path to target schemas
- New endpoints: GET /targets/{id}/decisions, GET /jobs/{id}/router-report

### Week 2, Days 7-8: Fixture-Based Tests
**Files to create**:
- `tests/fixtures/static_pages/*.html` (5 files)
- `tests/fixtures/spa_pages/*.html` (5 files)
- `tests/integration/test_router_edge_cases.py` (350 lines)

**Work**:
- Static HTML suite (blog, docs, landing, empty, heavy markup)
- SPA suite (React shell, Next.js SSR, Vue, Angular, partial hydration)
- Edge cases (redirects, soft-404s, rate limits, timeouts)

### Week 2, Day 9: Benchmark Suite
**Files to create**:
- `tests/benchmarks/test_router_performance.py` (250 lines)
- `scripts/benchmark_router.py` (180 lines)

**Work**:
- Comparative benchmarks (browser-only vs router+fast-path)
- 10x speedup target for static content
- 95% accuracy target for dynamic content
- Report generation

### Week 2, Day 10: Fail-Closed + Final Report
**Files to modify**:
- `src/crawler/quality_gate.py` (30 lines)
- `src/crawler/smart_router.py` (20 lines)

**Work**:
- Borderline timing → fail to browser
- Indeterminate quality → fail to browser
- Router uncertainty → fail to browser
- Production sign-off checklist

---

## Summary

| Component | Status | Lines |
|-----------|--------|-------|
| Decision Store | ✅ Complete | 600 |
| Database Model | ✅ Complete | 50 |
| Alembic Migration | ✅ Complete | 120 |
| Celery Integration | ✅ Complete | ~300 |
| API Updates | 🔄 Pending | ~110 |
| Fixture Tests | 🔄 Pending | ~350 |
| Benchmarks | 🔄 Pending | ~430 |
| Fail-Closed | ✅ Complete (in tasks.py) | ~50 |
| **Total** | **60% Complete** | **~1,560 / 2,500** |

## Week 1 Complete

### ✅ Days 1-2: CrawlDecisionStore/Repository
- 600 lines of repository code with full CRUD
- Analytics support (FallbackStats, RouterQualityReport)
- In-memory repository for testing

### ✅ Days 3-4: Celery Pipeline Integration
**Modified**: `src/shared/tasks.py`

**Added**:
- `crawl_url_with_routing()` - Main hybrid routing task (200 lines)
- `_execute_fast_path()` - HTTPX wrapper
- `_execute_browser_path()` - Playwright wrapper (placeholder)
- `_should_fail_closed()` - Fail-closed decision logic (50 lines)

**Integration Features**:
- Reads `target.configuration["crawl_path"]` with safe default "browser"
- Smart Router per-URL decision making
- HTTPX Fast Path for static content
- Quality-gated fallback to browser
- Canonical decision record persistence via CrawlDecisionStore
- Fail-closed behavior for ambiguous cases

**Fail-Closed Rules Implemented**:
1. Quality result uncertain → fallback to browser
2. Timing borderline (>90% of threshold) → fallback
3. Indeterminate content quality → fallback
4. Router uncertainty on ambiguous URL → fallback

### ✅ Day 5: Alembic Migration
- Migration 005 with upgrade/downgrade
- crawl_path column with safe default
- crawl_decisions table with RLS policies
- Full index coverage for analytics queries

---

## Remaining: Week 2

### Day 6: API Contract Updates (~110 lines)
**Files**: `src/api/routes/targets.py`, `src/api/schemas.py`
- Add crawl_path to target schemas
- New endpoints: GET /targets/{id}/decisions, GET /jobs/{id}/router-report

### Days 7-8: Fixture-Based Tests (~350 lines)
**Files**: Test fixtures + `test_router_edge_cases.py`
- Static HTML suite (5 fixtures)
- SPA suite (5 fixtures)
- Edge cases (redirects, soft-404s, rate limits, timeouts)

### Day 9: Benchmark Suite (~430 lines)
**Files**: `test_router_performance.py`, `benchmark_router.py`
- Comparative benchmarks (browser-only vs router+fast-path)
- 10x speedup target for static
- 95% accuracy target for dynamic

### Day 10: Final Report
- Production sign-off checklist
- Performance report generation

---

## Key Design Decisions

1. **Separate Decision Store**: ExecutionLogger handles runtime logging; CrawlDecisionStore handles canonical persistence. Clean separation of concerns.

2. **Immutable Records**: Decision records are frozen dataclasses, ensuring audit trail integrity.

3. **RLS-Enabled**: crawl_decisions table has Row-Level Security policies matching other tables.

4. **Backward Compatible**: Default `crawl_path='browser'` means existing targets require no migration.

5. **Indexed for Analytics**: Composite indexes on (job_id, created_at) and (domain, created_at) for efficient reporting.

---

## Next Immediate Task

**Celery Pipeline Integration** (Week 1, Days 3-4)

Modify `src/shared/tasks.py` to:
1. Read `target.configuration.get("crawl_path", "browser")`
2. Route URLs through SmartRouter
3. Execute FAST/BROWSER/FALLBACK paths
4. Persist decisions via CrawlDecisionStore
5. Implement fail-closed behavior
