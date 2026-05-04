# Skills Index

This index catalogs all available skills in the `.windsurf/skills/` directory. Skills are reusable capability modules that agents can invoke programmatically.

For skill authoring specifications, see [SKILL_SCHEMA.md](./SKILL_SCHEMA.md).

---

## Quality Debt & Code Hygiene

### contract-enforcement-auditor
**Description:** Scan for contract violations and enforcement gaps across all 6 canonical contracts in contract.md
**When to Use:** Auditing compliance, checking ESLint rule status, verifying CI gate blocking, assessing gap between documented contracts and runtime enforcement
**Side Effects:** read
**Related Workflow:** `/contract-enforcement-auditor`

### dead-code-sweeper
**Description:** Identify and safely remove dead code including orphan pages, unreachable routes, unused exports, mock data blocks
**When to Use:** Cleaning up codebase, after major refactors, when FRONTEND_AUDIT_REPORT.md dead code list needs action
**Side Effects:** write
**Related Workflow:** `/dead-code-sweeper`

### deprecation-migrator
**Description:** Migrate deprecated anti-pattern instances to canonical replacements defined in contract.md
**When to Use:** Fixing tenant-id-as-parameter, direct-header-access, explicit-db-connect, inline-middleware patterns
**Side Effects:** write
**Related Workflow:** `/deprecation-migrator`

### dil-hook-scaffolder
**Description:** Scaffold TanStack Query hooks for DIL (Data Intelligence Layer) backend services with zero frontend integration
**When to Use:** Building frontend hooks for products, evidence, competitive-intel, roi, enrichment services
**Side Effects:** write
**Related Workflow:** `/dil-hook-scaffolder`

### facade-page-connector
**Description:** Rewire frontend pages from static/mock data or generic useWorkspaceTabQuery to real backend hooks
**When to Use:** Page renders hardcoded data, uses MOCK_ arrays, connects to generic workspace endpoint
**Side Effects:** write
**Related Workflow:** `/facade-page-connector`

### tool-contract-sync
**Description:** Audit and fix the three-way sync between tool implementations, skill definitions, and tool manifests
**When to Use:** Tools registered in ToolRegistry but missing skill MDs or JSON Schema manifests
**Side Effects:** write
**Related Workflow:** `/tool-contract-sync`

---

## Testing & Quality Assurance

### autonomous-test-assurance
**Description:** Level 4 autonomous agent for end-to-end test assurance with self-directed discovery and automatic recovery
**When to Use:** Comprehensive test suite transformation into production assurance without human checkpoints
**Related Workflow:** `/autonomous-test-assurance-agent`

### test-quality-auditor
**Description:** Evaluate test suites against quality principles and safely rewrite tests for Python/pytest and TypeScript/Vitest
**When to Use:** Auditing test quality, applying targeted rewrites, resolving failures
**Related Workflow:** `/test-quality-remediation`

### pytest
**Description:** Python testing with pytest including fixtures, parametrization, markers, mocking, and async testing patterns
**When to Use:** Writing or refactoring Python tests

### playwright
**Description:** End-to-end test automation with Playwright for TypeScript, JavaScript, Python, Java, and C#
**When to Use:** E2E testing, local execution, cloud testing, POM patterns, CI/CD integration

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

---

## Architecture & Governance

### pre-production-audit
**Description:** Conduct comprehensive pre-production audits of enterprise SaaS platforms
**When to Use:** Preparing for production deployment, reviewing code quality, assessing security posture
**Related Workflow:** `/pre-production-audit`

### contract-enforcement-auditor
*(See above under Quality Debt)*

### tool-contract-sync
*(See above under Quality Debt)*

### code-boundary-enforcement
**Description:** Enforce strict boundary discipline between domains, dependencies, and system layers
**When to Use:** Ensuring separation between internal domains, external dependencies, and system layers
**Related Workflow:** `/code-boundary-enforcement`

---

## Frontend & UX

### agentic-ux
**Description:** UI patterns for agent-driven interfaces including streaming responses, tool execution visibility, confirmation flows, and progress indication
**When to Use:** Building AI-powered user interfaces

### login-signup-ux
**Description:** Best practices for designing, building, and testing login and signup flows with strong UX, accessibility, security, and OAuth integration
**When to Use:** Implementing authentication flows

### shadcn-fabric
**Description:** shadcn/ui usage guidelines for Value Fabric frontend
**When to Use:** Using shadcn/ui components

### facade-page-connector
*(See above under Quality Debt)*

### frontend-audit-refactor
**Description:** Audit a React/TypeScript frontend codebase and its backend API connections, then apply iterative refactoring loops
**When to Use:** Auditing frontend, reviewing backend connections, finding and removing stale code

### react-component-design
**Description:** Three-phase React component design workflow with chain-of-thought rigor
**When to Use:** Designing React components with agent skills

### component-self-review
**Description:** Post-generation code review workflow for enterprise-grade component validation
**When to Use:** After component generation but before merging

---

## AI & Orchestration

### orchestration
**Description:** LangGraph-based workflow orchestration for multi-step agent processes with state management, checkpointing, and human-in-the-loop integration
**When to Use:** Building multi-step AI workflows

### autonomous-test-assurance
*(See above under Testing & Quality Assurance)*

### memory-context
**Description:** Vector store and knowledge graph integration for semantic memory, conversation context management, and cross-session persistence
**When to Use:** Implementing memory systems for AI agents

### structured-outputs
**Description:** Pydantic-based structured output validation and LLM response parsing with OpenAI/Anthropic function calling and JSON schema enforcement
**When to Use:** Parsing structured outputs from LLMs

---

## Documentation

### technical-documentation
**Description:** Professional technical documentation generation and maintenance workflow
**When to Use:** Creating documentation for new systems or APIs, when docs are outdated, for handoffs
**Related Workflow:** `/technical_documentation`

### fumadocs
**Description:** Fumadocs documentation framework guidelines
**When to Use:** Working with Fumadocs documentation system
**Related Workflow:** `/fumadocs-drift-audit`

### cleanup-docs
**Description:** Monorepo documentation cleanup workflow
**When to Use:** Cleaning up scattered documentation, consolidating docs
**Related Workflow:** `/cleanup-docs`

---

## Infrastructure & DevOps

### gate-hardening
**Description:** Build machine-verifiable production release gate system using TDD
**When to Use:** Codebase needs ship/no-ship test gates for tenant isolation, state consistency, degraded dependencies
**Related Workflow:** `/gate-hardening`

### drift-assessment
**Description:** Multi-layer drift detection for API contracts, schemas, and behavior drift
**When to Use:** After code changes touching API routes or schemas, before releases, weekly drift reports
**Related Workflow:** `/drift-assessment`

### value-engine-e2e-validation
**Description:** Bootstrap the full development stack, seed a demo tenant and user, authenticate, execute the complete Value Engine workflow end-to-end
**When to Use:** End-to-end validation of the Value Engine

---

## Evaluation & Metrics

### evals
**Description:** Evaluation frameworks for agent performance, output quality, and extraction accuracy with metrics collection and regression testing
**When to Use:** Evaluating agent performance, measuring output quality

---

## Skill Maintenance

**Last Updated:** 2026-05-04

**Total Skills:** 38

**Skills with Full Frontmatter:** 3 (contract-enforcement-auditor, deprecation-migrator, dead-code-sweeper)

**Skills Needing Frontmatter Updates:** 35 remaining

**Note:** This index is generated manually. Consider automating this index generation by parsing SKILL.md frontmatter from all skill directories.
