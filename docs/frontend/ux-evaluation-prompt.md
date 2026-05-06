# Fabric_4L Frontend UI/UX Evaluation Prompt

**Copy this prompt and provide it to an AI agent to conduct a comprehensive frontend evaluation.**

---

## Context

You are evaluating the Fabric_4L frontend application, an enterprise SaaS platform for value intelligence and business case generation. The frontend is located at `apps/web/` and is built with React, TypeScript, Vite, and TanStack Query.

## Architecture Overview

Fabric_4L follows a six-layer backend architecture (L1-L6) with a three-tier frontend hook system:

- **Tier 1 (Protocol Hooks):** HTTP mechanics + Zod validation in `src/api/protocol/`
- **Tier 2 (Domain Hooks):** React Query wrappers for bounded contexts in `src/hooks/`
- **Tier 3 (Page Hooks):** Compose domain hooks into page-specific shapes in `src/hooks/pages/`

## Evaluation Scope

Conduct a comprehensive UI/UX evaluation across the following dimensions:

### 1. Contract Compliance

Evaluate adherence to the three ratified frontend contracts:

**Contract A: API Boundary Contract** (`contracts/frontend/01-api-boundary-contract.md`)
- All HTTP traffic passes through `apiClient.ts` (no direct axios/fetch imports)
- Error responses normalized to `FabricApiError` shape
- Standardized pagination with `PaginatedResponse<T>` shape
- Retry policy with exponential backoff for retryable errors
- Zod schema validation on all mutation requests

**Contract B: Type Synchronization Contract** (`contracts/frontend/02-type-synchronization-contract.md`)
- Backend API types generated from OpenAPI specs in `src/api/generated/`
- No manually authored types for backend shapes
- Frontend-owned types (UI state, view models, forms) in `src/types/`
- Type generation pipeline: `pnpm run generate:types`

**Contract C: Hook Architecture Contract** (`contracts/frontend/03-hook-architecture-contract.md`)
- Three-tier hook system properly implemented
- Query keys use `QK.{domain}.{action}` convention from `src/hooks/queryKeys.ts`
- Domain hooks use `useFabricQuery`/`useFabricMutation` wrappers
- Mutations invalidate appropriate query keys
- No page components call `fetch` directly
- No mock data after migration window

### 2. Known Technical Debt

Review the status of known issues from `apps/web/FRONTEND_CLEANUP_SUMMARY.md`:

- **Imperative Navigation:** 82 instances of `useNavigate()` across 46 files (should use state-based navigation)
- **Inline Tool Definitions:** 19 instances of tools defined as lambdas (should use ToolRegistry)
- **URL Concatenation:** 7 remaining instances of string concatenation for paths
- **DIL Integration Gaps:** 52 unintegrated backend endpoints across 8 DIL services (products, evidence, competitive-intel, roi, enrichment, value-hypotheses, narratives, intelligence)

### 3. UI/UX Quality Assessment

Evaluate the user experience across these dimensions:

**Navigation & Information Architecture**
- Route structure clarity and discoverability
- Breadcrumb implementation and accuracy
- Navigation state management (URL state vs component state)
- Deep linking support

**Component Design**
- Component reusability and consistency
- shadcn/ui component usage patterns
- Custom component quality and accessibility
- Loading states and error boundaries

**Data Presentation**
- List views and pagination UX
- Detail views and information hierarchy
- Empty states and no-data scenarios
- Real-time data updates and streaming

**Form Design**
- Form validation feedback
- Multi-step workflows
- Save/draft functionality
- Error recovery patterns

**Performance**
- Initial load time and bundle size
- Route transition speed
- Data fetching efficiency (waterfall analysis)
- Client-side rendering vs server-side needs

**Accessibility**
- Keyboard navigation
- Screen reader compatibility
- Color contrast ratios
- Focus management

### 4. Page-by-Page Review

Systematically review key pages in `src/pages/`:

**Core Workflows**
- Login/authentication flow
- Workspace/dashboard
- Value Studio (formula builder, hypothesis creation)
- Prospect setup and enrichment
- Business case generation
- Document export workflows

**Data Management**
- Account list and detail views
- Product portfolio views
- Evidence library
- Competitive intelligence
- ROI calculator

**Settings & Admin**
- User preferences
- Tenant configuration
- Integration settings

### 5. Integration Quality

Evaluate backend integration patterns:

- Hook coverage for DIL endpoints (52 unintegrated endpoints identified)
- Error handling consistency across hooks
- Loading state patterns
- Optimistic updates implementation
- Cache invalidation strategies

## Output Format

Provide your evaluation in the following structure:

### Executive Summary
- Overall assessment (P0/P1/P2 issues)
- Critical blockers for production
- Top 3 UX priorities

### Contract Compliance Report
- Contract A (API Boundary): [PASS/FAIL/PARTIAL] with evidence
- Contract B (Type Sync): [PASS/FAIL/PARTIAL] with evidence
- Contract C (Hook Architecture): [PASS/FAIL/PARTIAL] with evidence

### Technical Debt Status
- Imperative navigation: [X/82 instances resolved]
- Inline tool definitions: [X/19 instances resolved]
- URL concatenation: [X/7 instances resolved]
- DIL integration: [X/52 endpoints integrated]

### UI/UX Findings by Dimension
For each dimension (Navigation, Component Design, Data Presentation, etc.):
- Strengths
- Weaknesses
- Specific issues with file paths and line numbers
- Severity (Critical/High/Medium/Low)

### Page-Specific Issues
For each key page reviewed:
- Page name and location
- UX issues found
- Technical issues found
- Recommended improvements

### Prioritized Action Plan
1. **P0 (Critical - Blocker):** Issues that must be fixed before production
2. **P1 (High - Major):** Significant UX/technical issues
3. **P2 (Medium - Important):** Improvements for polish
4. **P3 (Low - Nice to have):** Enhancements

Each action item should include:
- Description
- File/location reference
- Estimated effort
- Dependencies

### Design System Recommendations
- Component library gaps
- Design inconsistencies
- Accessibility improvements needed
- Performance optimization opportunities

## Evaluation Guidelines

- Be specific: Reference exact file paths, component names, and line numbers where possible
- Be actionable: Provide concrete recommendations, not vague suggestions
- Be pragmatic: Consider technical debt and migration constraints
- Be user-centric: Evaluate from the perspective of B2B SaaS users (sales, product managers, analysts)
- Reference existing contracts and documentation when citing violations

## Access to Codebase

The frontend codebase is located at:
- Root: `apps/web/`
- Source: `apps/web/src/`
- Contracts: `contracts/frontend/`
- Cleanup summary: `apps/web/FRONTEND_CLEANUP_SUMMARY.md`

Begin your evaluation by reading the key contracts and documentation, then systematically review the codebase structure and implementation.
