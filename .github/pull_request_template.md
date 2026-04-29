## Summary

- Describe what changed and why.

## Change Type

- [ ] Feature
- [ ] Bug fix
- [ ] Documentation
- [ ] Refactor/maintenance

## Release & Policy Checklist (Required)

- [ ] If API behavior/contracts changed, I updated `contracts/openapi/` and/or `contracts/jsonschema/`.
- [ ] If API changes are breaking, I created/updated a major version and included migration guidance.
- [ ] If deprecating APIs, I documented deprecation start and sunset dates per `docs/api-versioning-policy.md`.
- [ ] I reviewed DR expectations in `docs/reliability/dr-policy.md` and updated recovery docs if service criticality changed.
- [ ] For resilience-impacting changes, I updated or validated DR runbooks in `docs/runbooks/`.

## Validation

- [ ] `make verify`
- [ ] `make evals` (required for agent/skill prompt changes)

## Code Quality Checklist

- [ ] Accessibility checks passed (`pnpm run test:a11y:components`, `pnpm run test:a11y:pages`, `pnpm run test:a11y:gate`).
- [ ] Keyboard navigation acceptance criteria validated for changed UX flows.
- [ ] Screen-reader announcements/labels validated for changed UX flows.
- [ ] If requesting a temporary accessibility exception, linked remediation ticket + due date.
- [ ] No unused imports (ruff F401)
- [ ] No unused variables (ruff F841)
- [ ] No `console.log` in production code (without DEV guard)
- [ ] All TODOs reference a ticket (TODO: TICKET-123 format)
- [ ] No dead code blocks (commented-out code > 3 lines)

## Risks / Rollback

- Known risks:
- Rollback plan:
