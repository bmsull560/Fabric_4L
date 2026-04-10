---
description: Full workflow to assess current roadmap state and propose concrete additions for production-complete product
---

# Propose Roadmap Additions Workflow

Use this workflow to systematically assess the current ROADMAP.md state and propose concrete, prioritized additions that align with production-complete goals.

## Activation Criteria

Manual activation:
- Sprint planning sessions
- Pre-release readiness reviews
- Quarterly roadmap updates
- When adding new layers or major features

## Workflow Steps

1. **Initialize Context**
   // turbo
   - Read `ROADMAP.md` from repository root using `read_file`
   - Read any existing gap analysis reports from `.windsurf/plans/`
   - Extract production-ready criteria from "Definition of Production Ready" section
   - Identify layer structure (L1-L5, FRONTEND, DEVOPS) and current completion state
   - Map task dependencies based on "Unblocks" or "Depends on" fields in existing tasks

2. **Assess Current State**
   - Count completed vs pending tasks per layer
   - Identify tasks with missing acceptance criteria
   - Flag placeholder implementations (stubs, TODOs, empty functions)
   - Calculate completion percentage per layer and overall

3. **Identify Production Blockers**
   - Check each criterion in production-ready table:
     - End-to-end workflow complete
     - All APIs responding (not stubs)
     - Frontend showing real data
     - Tests passing (>80% coverage)
     - Docker deployment working
     - Monitoring configured
   - Map blockers to specific roadmap gaps

4. **Generate Concrete Proposals**
   For each identified gap, create:
   - **Task Title**: Clear, actionable description
   - **Layer**: L1-L5, FRONTEND, or DEVOPS
   - **Priority**: P0 (critical path), P1 (important), P2 (nice-to-have)
   - **Effort**: Estimated days
   - **Unblocks**: What downstream work this enables
   - **Acceptance Criteria**: 3-5 bullet points
   - **Implementation Hints**: Key files to modify/create

5. **Sequence by Dependencies**
   - Order proposals using dependency graph
   - Ensure upstream blockers are addressed first
   - Group parallelizable work into tracks

6. **Format for ROADMAP.md**
   - Structure as new prioritized tasks
   - Include effort estimates and acceptance criteria
   - Add to appropriate section (existing prioritized tasks or new additions)
   - Follow existing markdown format patterns

7. **Present for Approval**
   - Display proposed additions formatted for review
   - Show before/after completion percentages per layer
   - Highlight critical path items with rationale
   - Explicitly ask user: "Approve these additions to ROADMAP.md?"
   - Await explicit "yes" before proceeding

8. **Apply Updates (on explicit approval only)**
   // turbo
   - Insert approved tasks into `ROADMAP.md` using `edit` or `multi_edit`
   - Update completion percentages in roadmap headers
   - Refresh "Definition of Production Ready" status table
   - Run `git add ROADMAP.md` to stage changes
   - Confirm to user: "Changes staged. Run `git commit` to finalize."

## Constraints

- **Maximum 5 P0 tasks**: Prevent over-prioritization
- **Time-boxed**: Proposals must fit within 4-week horizon by default
- **Dependency-aware**: Never propose downstream work before upstream blockers
- **Measurable**: Every proposal must have verifiable acceptance criteria

## Output Format

```markdown
## Proposed Roadmap Additions

Generated: {YYYY-MM-DD} | Target: Production Complete ({target}%)

### Track A: Backend Core (2 weeks)

#### Task N: [Title] (P0)
- **Layer**: L2
- **Effort**: 2 days
- **Unblocks**: GraphRAG queries
- **Acceptance Criteria**:
  - [ ] Criterion 1
  - [ ] Criterion 2
- **Implementation**:
  - Modify: `file.py`
  - Create: `new_file.py`
```

## Execution Log Format

Present progress using this structured format:

```
[INIT] Reading ROADMAP.md - Current overall: ~{N}% complete
[ANALYZE] Production criteria: {N}/{total} met
[GAPS] Found {N} blocking gaps, {N} non-blocking
[PROPOSE] Generated {N} P0 tasks, {N} P1 tasks, {N} P2 tasks
[SEQUENCE] Ordered by dependency graph - {N} parallel tracks identified
[REVIEW] Presenting to user for approval...
[APPLY] User approved {N}/{total} tasks - Updating ROADMAP.md
[COMPLETE] Roadmap updated, {N} new tasks added, staged for commit
```

## Concrete Actions Checklist

Ensure measurable outcomes with this checklist:

- [ ] Read and analyzed current `ROADMAP.md` state
- [ ] Identified at least one existing gap analysis report or created one
- [ ] Calculated completion percentages per layer
- [ ] Generated minimum 3 concrete, prioritized tasks
- [ ] Every P0 task has 3-5 verifiable acceptance criteria
- [ ] Identified unblocks/dependencies for each proposed task
- [ ] Presented proposals to user and awaited explicit approval
- [ ] Only after approval: modified `ROADMAP.md`
- [ ] Verified formatting matches existing roadmap style
- [ ] Staged changes for user commit

## Safety Rules

1. **Never modify ROADMAP.md without explicit user approval**
2. **Preserve existing task structure and formatting**
3. **Do not delete existing tasks** - only add new ones
4. **Maintain dependency graph accuracy** when adding tasks
5. **Log all proposed changes** with rationale
