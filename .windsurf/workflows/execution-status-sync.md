---
description: Task-level roadmap execution audit with integrity checks and next engineering work package generation
---

# Execution Status Sync Workflow

Use this workflow to produce an evidence-based roadmap update at the **task level**, detect broken cross-layer integrations, and generate the next **assignment-ready engineering work package**.

## Activation Criteria

Manual activation:
- Daily/weekly execution sync
- Before sprint planning
- Before marking major tasks "Complete"
- After cross-layer refactors

## Workflow Steps

1. **Load Task Inventory**
   // turbo
   - Read `ROADMAP.md`
   - Enumerate tasks (Task N blocks) and extract: title, status text, dependencies, acceptance criteria
   - Normalize each task to one layer label: `L2`, `L3`, `L4`, `Frontend`

2. **Collect Ground Truth Evidence**
   - For each in-scope task, verify completion strictly using:
     - Code exists in referenced files/modules
     - Tests exist for the behavior
     - Tests execute and pass (or explicitly fail)
     - Integration path is wired (not isolated/local only)
   - Record evidence paths and command output snippets used for each conclusion

3. **Assign Task-Level Execution Status**
   - Assign one status per task:
     - `Not Started`
     - `In Progress`
     - `Blocked`
     - `Complete`
   - Assign `owner` if explicitly known in roadmap/docs; otherwise use `Unassigned`
   - Do not mark `Complete` unless all strict checks pass

4. **Run System Integrity Check**
   - Validate real execution flows:
     - `L2 -> L3` ingestion
     - `L4` LangGraph workflow execution/resume path
     - `Frontend <-> API` connectivity and route contract alignment
   - Flag:
     - Broken integrations (API mismatch, import/runtime errors, schema drift)
     - Missing dependencies (upstream not ready)
     - Boundary violations (cross-layer coupling, import side effects)
     - Hidden work (retry logic, error handling, persistence, operational hardening)

5. **Detect False Completes**
   - For every task currently labeled complete in roadmap text, attempt real validation
   - If runtime/contract checks fail, downgrade to `Blocked` or `In Progress` with rationale

6. **Select Next Execution Slice (1-3 days)**
   - Choose the highest-leverage slice that:
     - unblocks downstream tasks,
     - delivers a real end-to-end capability,
     - is shippable and testable within 1-3 days
   - Provide explicit rationale for why this slice wins over alternatives

7. **Generate Assignment-Ready Work Package**
   - Output:
     - Objective (single clear outcome)
     - Atomic tasks
     - Affected files/modules
     - Dependencies
     - Risks/edge cases
     - Acceptance criteria including real execution checks (not build-only)

8. **Persist Outputs in `.windsurf/plans`**
   // turbo
   - Create/update a timestamped report in `.windsurf/plans/` (e.g., `execution-status-sync-YYYYMMDD-HHMM.md`)
   - Include:
     - Task table
     - Critical blockers
     - Selected slice
     - Work package
   - If user approves, update `ROADMAP.md` to reflect validated status labels and notes

## Required Output Format

1. **Task-level roadmap table** (`status`, `owner`, `layer`)
2. **Critical blockers / broken integrations**
3. **Selected execution slice** (with why)
4. **Assignment-ready work package**

## Status Rules

Use this decision guide for each task:

- **Complete**
  - Code exists
  - Relevant tests exist and pass
  - Cross-layer integration executes successfully
- **Blocked**
  - Clear dependency/integration failure prevents completion
- **In Progress**
  - Meaningful implementation exists but strict completion criteria not fully met
- **Not Started**
  - No meaningful code path or contract implementation exists

## Concrete Checklist

- [ ] Parsed all roadmap tasks in scope
- [ ] Assigned normalized layer to each task
- [ ] Gathered evidence from code + tests + runtime checks
- [ ] Produced strict status assignment per task
- [ ] Identified broken integrations and dependency blockers
- [ ] Flagged any false-complete tasks
- [ ] Selected one 1-3 day execution slice
- [ ] Produced assignment-ready package
- [ ] Saved report in `.windsurf/plans/`

## Safety Rules

1. Never mark a task `Complete` without execution evidence.
2. Prefer runtime/integration truth over narrative summary docs.
3. Preserve roadmap structure; only update statuses/notes unless explicitly asked for larger edits.
4. Keep scope to highest-leverage slice; avoid parallel overcommitment.
5. Capture assumptions explicitly when evidence is unavailable.
