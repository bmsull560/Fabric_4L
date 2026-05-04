# Workflows Index

This index catalogs all available workflows in the `.windsurf/workflows/` directory. Workflows are orchestration patterns with explicit state machines for human-driven processes.

For workflow authoring specifications, see [WORKFLOW.md](./WORKFLOW.md).

---

## Quality Debt & Code Hygiene

### contract-enforcement-auditor
**Description:** Scans for contract violations and enforcement gaps across all 6 canonical contracts in contract.md
**When to Use:** Auditing compliance, checking ESLint rule status, verifying CI gate blocking, assessing gap between documented contracts and runtime enforcement
**Related Skill:** `skills/contract-enforcement-auditor/SKILL.md`

### dead-code-sweeper
**Description:** Identifies and safely removes dead code including orphan pages, unreachable routes, unused exports, mock data blocks
**When to Use:** Cleaning up codebase, after major refactors, when FRONTEND_AUDIT_REPORT.md dead code list needs action
**Related Skill:** `skills/dead-code-sweeper/SKILL.md`

### deprecation-migrator
**Description:** Migrate deprecated anti-pattern instances to canonical replacements defined in contract.md
**When to Use:** Fixing tenant-id-as-parameter, direct-header-access, explicit-db-connect, inline-middleware patterns
**Related Skill:** `skills/deprecation-migrator/SKILL.md`

### dil-hook-scaffolder
**Description:** Scaffolds TanStack Query hooks for DIL (Data Intelligence Layer) backend services with zero frontend integration
**When to Use:** Building frontend hooks for products, evidence, competitive-intel, roi, enrichment services
**Related Skill:** `skills/dil-hook-scaffolder/SKILL.md`

### facade-page-connector
**Description:** Rewires frontend pages from static/mock data or generic useWorkspaceTabQuery to real backend hooks
**When to Use:** Page renders hardcoded data, uses MOCK_ arrays, connects to generic workspace endpoint
**Related Skill:** `skills/facade-page-connector/SKILL.md`

### tool-contract-sync
**Description:** Audit and fix the three-way sync between tool implementations, skill definitions, and tool manifests
**When to Use:** Tools registered in ToolRegistry but missing skill MDs or JSON Schema manifests
**Related Skill:** `skills/tool-contract-sync/SKILL.md`

### code-boundary-enforcement
**Description:** Enforce strict boundary discipline between domains, dependencies, and system layers
**When to Use:** Ensuring separation between internal domains, external dependencies, and system layers

---

## Testing & Quality Assurance

### autonomous-test-assurance-agent
**Description:** Level 4 autonomous agent for end-to-end test assurance with self-directed discovery and automatic recovery
**When to Use:** Comprehensive test suite transformation into production assurance without human checkpoints

### test-quality-remediation
**Description:** Systematic test quality improvement across the repository with discovery, audit, rewrite, and validation phases
**When to Use:** Auditing test quality, applying targeted rewrites, resolving failures

---

## Code Review & Development

### jr-coder
**Description:** Implement a ticket, write tests, run them, commit, and mark ready for review
**When to Use:** Writing code for defined tasks

### jr-code-review
**Description:** Review a completed task for code quality, test coverage, and correctness
**When to Use:** Code is ready for review

### jr-architect-review
**Description:** Review a completed feature for cross-task coherence, integration quality, and architectural soundness
**When to Use:** All tasks in a feature are done before merging

### jr-plan
**Description:** Break down a plan document into features and tasks with dependencies
**When to Use:** Starting new work or scoping a project

### jr-rebase
**Description:** Resolve git rebase conflicts in feature branches
**When to Use:** Rebase has conflicts that need resolution

### jr-retro
**Description:** Post-mortem analysis of a completed or in-progress feature
**When to Use:** Feature shipped, stalled, or after architect review

### refinement
**Description:** Transform functional code into production-grade output through systematic inspection and direct fixes
**When to Use:** Improving code quality after implementation

---

## Architecture & Governance

### pre-production-audit
**Description:** Conduct comprehensive pre-production audits of enterprise SaaS platforms
**When to Use:** Preparing for production deployment, reviewing code quality, assessing security posture

### drift-assessment
**Description:** Multi-layer drift detection for API contracts, schemas, and behavior drift
**When to Use:** After code changes touching API routes or schemas, before releases, weekly drift reports

### execution-status-sync
**Description:** Task-level roadmap execution audit with integrity checks and next engineering work package generation
**When to Use:** Daily/weekly execution sync, before sprint planning, before marking major tasks complete

---

## Frontend & UX

### react-component-design
**Description:** Three-phase React component design workflow with chain-of-thought rigor
**When to Use:** Designing React components with agent skills

### component_self_review
**Description:** Post-generation code review workflow for enterprise-grade component validation
**When to Use:** After component generation but before merging

### frontend-audit-refactor
**Description:** Audit a React/TypeScript frontend codebase and its backend API connections, then apply iterative refactoring loops
**When to Use:** Auditing frontend, reviewing backend connections, finding and removing stale code

---

## Documentation

### technical_documentation
**Description:** Professional technical documentation generation and maintenance workflow
**When to Use:** Creating documentation for new systems or APIs, when docs are outdated, for handoffs

### fumadocs-drift-audit
**Description:** Audit Fumadocs documentation drift for ongoing maintenance and migration
**When to Use:** Post-release, periodic maintenance, pre-migration, when docs appear out of sync

### cleanup-docs
**Description:** Monorepo documentation cleanup workflow
**When to Use:** Cleaning up scattered documentation, consolidating docs

---

## Infrastructure & DevOps

### gate-hardening
**Description:** Build machine-verifiable production release gate system using TDD
**When to Use:** Codebase needs ship/no-ship test gates for tenant isolation, state consistency, degraded dependencies

### value-engine-e2e-validation
**Description:** Bootstrap the full development stack, seed a demo tenant and user, authenticate, execute the complete Value Engine workflow end-to-end
**When to Use:** End-to-end validation of the Value Engine

### production_only_delivery
**Description:** Ensure all implementation work results in real, production-grade code with no mock, stub, placeholder, simulated, or shortcut behavior
**When to Use:** Enforcing production-only delivery standards

---

## Planning & Roadmap

### propose-roadmap-additions
**Description:** Full workflow to assess current roadmap state and propose concrete additions for production-complete product
**When to Use:** Sprint planning, pre-release readiness reviews, quarterly roadmap updates

### launch-readiness-assessment
**Description:** Fabric_4L Dual-Track Launch Readiness Assessment & Sprint Plan using claimed-versus-verified evidence
**When to Use:** Pre-release readiness reviews, quarterly roadmap updates

---

## Orchestration Patterns (Templates)

### _templates/human-in-the-loop
**Pattern:** Human-in-the-Loop
**Description:** Agent generates diff, stops, notifies human, resumes only after approval
**Use Cases:** Auth/billing changes, database schema migrations, API contract breaking changes, security policy modifications

### _templates/manager-worker
**Pattern:** Manager-Worker
**Description:** Decompose large refactoring by project graph; workers execute in parallel; manager validates
**Use Cases:** Large refactoring tasks, parallel code transformations

### _templates/pipeline-dag
**Pattern:** Pipeline (DAG)
**Description:** Multi-stage pipeline where each stage is an agent with explicit input/output contracts
**Use Cases:** Multi-stage processes with dependencies between stages

---

## Automation & Triggers

### autonomous_code_reviewer_trigger
**Description:** Auto-trigger code review on save or periodic check
**When to Use:** Enable auto-review for continuous code quality monitoring

---

## Workflow Templates

### WORKFLOW.md
**Description:** Workflow authoring specification for structured orchestration patterns
**When to Use:** Creating new workflows with proper state management and circuit breakers

---

## Workflow Maintenance

**Last Updated:** 2026-05-04

**Total Workflows:** 27 (24 main workflows + 3 templates)

**Workflows with Frontmatter:** 27/27 (100%)

**Workflows with Cross-References:** 3 (contract-enforcement-auditor, dead-code-sweeper, deprecation-migrator)

**Note:** This index is generated manually. Consider automating this index generation by parsing workflow frontmatter from all workflow files.
