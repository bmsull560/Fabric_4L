# Frontend Cleanup Rationale: Navigation Path Centralization

## ADR-Style Rationale

### Context
Frontend routing logic had drifted into multiple files with ad-hoc path construction patterns (string concatenation, local helper duplication, and mixed route-building conventions). This increased maintenance cost and made route contract compliance harder to enforce consistently.

### Decision
Adopt a **single navigation path-construction pattern** centered on the navigation service APIs (`getStatePath`, `buildPath`, and shared workspace-path resolution helpers), and route all workspace/account path assembly through that layer instead of per-component string composition.

### Why This Pattern
- **Contract consistency:** Aligns frontend navigation with route-state conventions rather than per-file URL construction.
- **Change isolation:** Route-shape changes can be made in one place instead of across many components.
- **Duplication reduction:** Removes repeated workspace path helper logic from layout and routing modules.
- **Static enforcement compatibility:** Centralized patterns are easier to check with CI policy gates.

### Consequences
- New routing code should prefer navigation service helpers over direct URL interpolation.
- Legacy wrappers may remain temporarily where they preserve compatibility; migration should proceed through focused follow-up changes rather than broad rewrites.
- Cleanup documentation should record architectural intent and enforcement links, not point-in-time claim snapshots.

---

## Scope of This Cleanup Record
- Frontend-only navigation/path-construction pattern standardization.
- This document is an architectural rationale record, **not** a live status dashboard.

---

## Current Enforcement / Status Sources
For current pass/fail state, use CI runs and canonical check definitions:

- GitHub Actions PR pipeline: `.github/workflows/pr-checks.yml`
- GitHub Actions test pipeline: `.github/workflows/test.yml`
- Frontend script definitions (type/lint/test/a11y/e2e): `apps/web/package.json`

These files are the source of truth for current check coverage and execution.

---

## Future Cleanup Doc Template
Use this template for subsequent frontend cleanup write-ups.

```md
# Frontend Cleanup: <short title>

<<<<<<< ours
### 2. Inline Tool Definitions (verification pending)
=======
## Rationale (ADR-style)
- **Context:** <what inconsistency or technical debt existed>
- **Decision:** <pattern adopted>
- **Why:** <why this pattern vs alternatives>
- **Consequences:** <what changes for future contributors>
>>>>>>> theirs

## Scope
- **In scope:** <areas/files/patterns intentionally addressed>
- **Out of scope:** <explicitly deferred items>

## Enforcement Link
- **CI / policy source of truth:** <repo path(s) to workflow/job/script>

## Ownership & Sunset
- **Owner:** <team or role>
- **Sunset / Revisit trigger:** <date, milestone, or condition>
```

