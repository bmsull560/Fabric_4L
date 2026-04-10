---
description: Analyze roadmap completion gaps and propose prioritized additions for production readiness
---

# Roadmap Update Skill

Use this skill to analyze the current ROADMAP.md, identify completion gaps, and propose prioritized additions to achieve production-complete status.

## Parameters

- `target_completion`: Target completion percentage (default: 95)
- `focus_areas`: Priority layers (L1, L2, L3, L4, L5, FRONTEND, DEVOPS)
- `time_horizon`: Weeks to production (default: 4)
- `blocking_only`: Only propose blocking items (default: false)

## Steps

1. **Read and Parse ROADMAP.md**
   - Load the current roadmap file
   - Extract completion percentages per layer
   - Identify "What's Missing" sections
   - Parse the dependency graph

2. **Assess Production Readiness**
   - Compare current state against "Definition of Production Ready" table
   - Identify unmet criteria (end-to-end workflow, API coverage, tests, etc.)
   - Flag blocking dependencies in the dependency graph

3. **Identify Critical Gaps**
   - Score gaps by: blocking factor × effort to fix × strategic value
   - Prioritize items that unblock downstream layers
   - Focus on gaps preventing end-to-end workflow completion

4. **Generate Proposed Additions**
   - Create concrete task descriptions with acceptance criteria
   - Estimate effort (days) for each proposed addition
   - Assign priority (P0/P1/P2) based on blocking impact
   - Group by layer and dependency order

5. **Validate Against Constraints**
   - Ensure proposals fit within `time_horizon`
   - Verify focus areas are respected
   - Check no duplicate tasks exist

## Output

Roadmap analysis report:
- Current completion summary per layer
- Unmet production criteria
- Prioritized list of proposed additions with:
  - Task description
  - Acceptance criteria (bullet format)
  - Estimated effort
  - Priority level
  - Dependencies
- Suggested insertion points in ROADMAP.md structure

## Example Use

"Analyze roadmap and propose additions to reach 95% completion in 3 weeks, focusing on L2 and L3"
"Identify blocking gaps preventing end-to-end workflow completion"
"Update roadmap with concrete tasks for Ground Truth Layer implementation"
