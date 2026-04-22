---
description: Post-generation code review workflow for enterprise-grade component validation
---

# Component Self-Review Workflow

Use this workflow after a component has been generated to perform rigorous self-critique and elevate the output from "functioning" to "enterprise-grade." This acts as a "Tech Lead Code Review" that validates the implementation against the original design.

## Prerequisites

- Component has been generated via `/react_component_design` or equivalent workflow
- Requirements Definition and Concept Design artifacts are accessible
- Code is in a reviewable state (files written or presented)

## When to Use

- **After Phase 3 completion:** Once code is generated but before merging
- **Before PR submission:** As a pre-review self-check
- **For legacy component audits:** When reviewing existing components for improvement opportunities

## Available Agent Skills

### 1. Analysis Skills
- **read_file**: Re-examine the generated code, requirements, and design documents
- **search_codebase**: Find related components to compare implementation patterns

### 2. Validation Skills
- **run_type_check**: Verify TypeScript strictness and type coverage
- **run_linter**: Check code style, unused imports, formatting
- **run_tests**: Execute component tests if they exist

### 3. Research Skills
- **web_search**: Verify accessibility best practices, performance patterns
- **fetch_documentation**: Check library-specific optimization techniques

### 4. Refinement Skills
- **write_file**: Implement the selected enhancements from Step 3
- **multi_edit**: Apply multiple improvements across files

## STEP 1: Gap Analysis & Alignment Check

**Objective:** Validate that implementation matches intent.

**Deliverables:**
1. **Requirements vs. Design Audit**
   - Review original Requirements Definition (Phase 1)
   - Verify Concept Design (Phase 2) addressed all edge cases and constraints
   - Flag any requirements that were ignored or inadequately addressed

2. **Design vs. Code Audit**
   - Compare generated code against proposed Component Hierarchy
   - Verify State Management matches the design (props vs. state decisions)
   - Check Styling Strategy adherence (did shortcuts occur?)
   - Document any "implementation drift" where code diverged from plan

**Skill Usage:**
- Use `read_file` to load the Requirements, Design, and Code artifacts
- Use `search_codebase` to compare against existing component patterns

## STEP 2: Future-Proofing & Scalability Review

**Objective:** Analyze non-functional requirements and technical debt.

**Review Dimensions:**

### Performance
- [ ] Unnecessary re-renders identified (missing `useMemo`, `useCallback`)
- [ ] Expensive computations not cached
- [ ] No lazy loading for heavy sub-components
- [ ] Large lists lack virtualization consideration

### Accessibility (a11y) & UX
- [ ] WCAG 2.1 compliance check (minimum AA)
- [ ] ARIA attributes present where needed
- [ ] Keyboard navigation fully functional
- [ ] Focus management correct (trap/return)
- [ ] Loading states are genuinely user-friendly (not jarring)
- [ ] Error states provide actionable feedback

### Maintainability
- [ ] Component coupling analysis (too tightly bound to parent?)
- [ ] TypeScript type robustness (no implicit `any`, no overly broad `object`)
- [ ] Single Responsibility Principle adherence
- [ ] Prop drilling eliminated (context used appropriately)
- [ ] Magic numbers/strings extracted to constants

**Skill Usage:**
- Use `run_type_check` to identify implicit `any` types or type coverage gaps
- Use `run_linter` to find code smells, unused code, complexity issues
- Use `web_search` for WCAG/a11y best practices if uncertain

## STEP 3: The Top 3 Enhancements

**Objective:** Extract exactly 3 high-impact improvement opportunities.

**For Each Enhancement, Document:**

1. **The Issue/Opportunity**
   - What is lacking or could be better?
   - Specific code location or pattern

2. **The "Why"**
   - Why does this matter?
   - Impact: performance, developer experience, user experience, bug prevention

3. **The Implementation Plan**
   - Brief technical explanation of the fix
   - Files that need modification
   - Any new dependencies or patterns to introduce

**Selection Criteria:**
- Must be actionable (not vague like "improve UX")
- Must have measurable impact (render time, bundle size, a11y score)
- Must not break existing contract (props API remains stable)

**Example Output:**
```
Enhancement 1: Memoize Expensive Graph Layout Calculation
- Issue: Graph nodes are recalculated on every render; O(n²) algorithm
- Why: Causes frame drops with >50 nodes; identified via React DevTools Profiler
- Plan: Wrap layout calculation in useMemo with [nodes, layoutType] deps
  - File: GraphExplorer.tsx lines 143-167
  - No new dependencies
```

## Execution Prompt Template

When invoking this workflow, use the following structure:

```
Execute the Component Self-Review Workflow on the component I just generated.

**COMPONENT LOCATION:**
- File path: [path to .tsx file]
- Test file: [path to .test.tsx if exists]

**ORIGINAL REQUIREMENTS & DESIGN:**
[Paste or reference the Phase 1 and Phase 2 artifacts if not in agent memory]

**FOCUS AREAS (optional):**
- Priority on: [performance / accessibility / maintainability]
- Known concerns: [any specific areas you want reviewed]

**AGENT DIRECTIVES:**
You MUST use run_type_check and run_linter to validate the current implementation. 
Present exactly 3 high-impact enhancements with implementation plans. Do not 
provide generic feedback—every suggestion must be specific and actionable.
```

## Post-Review Actions

After completing the review, you have several options:

### Option A: Implement All 3
```
Proceed with implementing enhancements 1, 2, and 3 from the review.
```

### Option B: Selective Implementation
```
Implement enhancement 2 only. The others are lower priority for now.
```

### Option C: Create Tickets
```
Convert the 3 enhancements into GitHub issue format for the backlog.
```

## Quality Checklist

- [ ] Step 1 completed: Requirements vs. Design vs. Code alignment verified
- [ ] Step 2 completed: Performance, a11y, maintainability analyzed
- [ ] Step 3 completed: Exactly 3 specific, high-impact enhancements identified
- [ ] Each enhancement has: Issue description, Justification, Implementation plan
- [ ] TypeScript and lint checks run and results considered
- [ ] No generic/fluff feedback (all suggestions are concrete)

## Relationship to Other Workflows

- **Preceded by:** `/react_component_design` (generates the component to review)
- **Followed by:** Implementation of selected enhancements
- **Alternative use:** Standalone audit of legacy components

## Why This Workflow Matters

| Without Review | With Review |
|--------------|-------------|
| Component "works" but has hidden perf issues | Re-renders identified and memoized |
| Accessibility gaps discovered in production | WCAG compliance verified pre-merge |
| Type safety degraded over time | Implicit `any` types caught early |
| Technical debt accumulates | 3 concrete improvements queued per component |
| Generic AI feedback ("looks good!") | Specific, actionable gap analysis |
