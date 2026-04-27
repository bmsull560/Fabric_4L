For a system of this scale and condition, the best approach is a **Contract-First Recovery Methodology** — treating the frontend not as a UI layer but as a **distributed system client** that needs architectural reconstruction. Here's the battle-tested framework:

---

## 1. The Tri-Track Audit (Week 1-2)

Before writing any design brief, run three parallel forensic audits:

### Track A: Surface Audit — "What's painted?"
Map every route to its **data source category**:
- **Green**: Live backend integration (real hooks, real types)
- **Yellow**: Generic endpoint passthrough (the single workspace hook problem)
- **Red**: Hardcoded mock / static / orphaned
- **Black**: No frontend surface exists for backend capability

Create a **Route Integrity Matrix** — a spreadsheet where each of the 157 routes is tagged with its data source type, hook name, and backend endpoint consumed. This immediately visualizes the 40% facade problem.

### Track B: API Archaeology — "What's buried?"
For those 50+ DIL endpoints with no frontend surface:
- Extract OpenAPI specs / Zod schemas from the backend
- Classify endpoints by domain entity (user, workspace, billing, etc.)
- Map CRUD operations and identify missing frontend types
- Flag endpoints that *should* power the orphan pages

### Track C: Contract Gap Analysis
Compare the existing 6 canonical contracts against:
- **API Boundary Contracts**: How does the frontend request data? What's the error handling protocol? How are pagination, filtering, sorting standardized?
- **Type Synchronization Contracts**: How do backend schema changes propagate to frontend?
- **Hook Architecture Contracts**: Standards for data fetching, caching, mutations, optimistic updates

---

## 2. The System Design Brief Structure

The brief itself should be 6 interconnected documents, not one monolithic file:

### Document 1: Integration Contract Specification
Define the **Frontend-Backend API Boundary**:
```typescript
// Example: Standardized hook contract
interface UseQueryHook<TRequest, TResponse> {
  queryKey: (params: TRequest) => string[];
  queryFn: (params: TRequest) => Promise<TResponse>;
  errorMapping: Record<number, UIErrorType>;
  staleTime: number;
  retryPolicy: RetryConfig;
}
```

**Key sections:**
- Endpoint-to-Hook mapping registry (all 50+ DIL endpoints assigned)
- Type generation pipeline (backend Zod → frontend TypeScript)
- Error boundary behavior per HTTP status code
- Loading state hierarchy (skeleton > spinner > cache)

### Document 2: Page Reality Index
For each of the 42 page components, a truth table:
| Page | Current State | Target State | Backend Dependency | Effort |
|------|--------------|--------------|-------------------|--------|
| Dashboard | Yellow (generic hook) | Green (dedicated DIL hooks) | 3 endpoints | M |
| Settings | Red (mock data) | Green | 2 endpoints | S |

Classify pages into:
- **Immediate wins** (hook exists, just needs wiring)
- **Medium build** (backend ready, frontend missing)
- **Deep refactor** (architectural mismatch)
- **Sunset candidates** (feature no longer needed)

### Document 3: Hook Architecture Blueprint
Establish the **three-tier hook system** you need:
1. **Protocol hooks** — The Zod-validated API client wrappers (lowest level)
2. **Domain hooks** — `useFabricQuery`, `useFabricMutation` with standard error handling, caching, and optimistic updates
3. **Page hooks** — Composed domain hooks for specific page data requirements, with proper loading/error state aggregation

Define strict rules: *No page component calls `fetch` directly. No page component uses mock data after T+30 days.*

### Document 4: Type Synchronization Protocol
Since you're Zod-based on the backend:
- Auto-generate TypeScript types from backend schemas at build time
- Version-lock frontend types to backend API versions
- Define breaking change detection (CI fails when backend schema changes without frontend type regeneration)

### Document 5: UI/UX Component Strategy
Beyond data, define:
- **Skeleton system** — Every async component must have a corresponding skeleton state
- **Error state taxonomy** — Network error vs. permission error vs. empty state, each with distinct UI patterns
- **Optimistic update patterns** — Where the UI pretends the backend succeeded before confirmation

### Document 6: Implementation Roadmap
Phase the work by **user impact**, not technical dependency:
- **Phase 1 (Sprint 1-3)**: Kill the mocks — wire the 6 orphan pages to real endpoints or delete them
- **Phase 2 (Sprint 4-8)**: Endpoint adoption — onboard the 50+ DIL endpoints using the new hook architecture
- **Phase 3 (Sprint 9-12)**: Refactor yellow pages — replace generic workspace hooks with dedicated domain hooks
- **Phase 4 (Ongoing)**: Constitution enforcement — CI gates that fail on mock data, missing types, or uncontracted endpoints

---

## 3. The Governance Model (Critical)

The "missing strategic constitution" is your root cause. Establish:

**The Contract Council** — A lightweight RFC process where:
- New backend endpoints cannot ship without a corresponding frontend hook specification
- Frontend pages cannot use mock data beyond the sprint they're introduced
- Contract.md is the source of truth, not the implementation

**CI Enforcement Gates**:
```yaml
# Example gates
- detect_mock_data: fail build if mock arrays/objects found in page components
- endpoint_coverage: fail if backend endpoint has no frontend hook after 2 sprints
- type_sync_check: fail if generated types are stale vs. backend schemas
```

**The "Facade Budget"** — Allow a maximum % of routes to be non-green (start at 40%, reduce by 10% per quarter until <5%).

---

## 4. Immediate Tactical Moves

While the brief is being written, start these parallel:

1. **Create a `contracts/api-boundary.md`** — Document the first 10 most critical DIL endpoints with their request/response types and intended frontend hooks
2. **Pick one orphan page** — Completely refactor it from mock → full backend integration as a **reference implementation**
3. **Generate types** — Set up the backend-to-frontend type generation pipeline so the integration gap becomes a mechanical problem, not an architectural one
4. **Add an integration dashboard** — A dev-only page showing endpoint coverage %, hook health, and mock data detection — make the invisible problem visible

---

## The Core Principle

Your frontend is currently a **stage set** — visually complete but structurally hollow. The design brief shouldn't just specify colors and components; it must establish **data integrity as a UX concern**. A page that renders mock data is a broken page, regardless of how polished it looks.

The brief's north star metric: **Functional Route Percentage** — the % of your 157 routes that render live, backend-sourced data with proper error and loading states. Track it weekly. Everything in the brief should move that number from 60% toward 95%.

