# Accessibility Statement and Remediation Process

## Target standard

Value Fabric targets **WCAG 2.1 Level AA** conformance for the frontend user experience.

## Continuous verification

Accessibility quality gates run in CI and locally:

- Component-level checks: `pnpm run test:a11y:components`
- Page-level checks: `pnpm run test:a11y:pages`
- CI thresholds: `pnpm run test:a11y:gate`

Current CI thresholds:

- Critical violations: `0` allowed
- Serious violations: `0` allowed
- Minimum scanned routes: `4`

## Exception handling

If a release needs a temporary accessibility exception:

1. Open a remediation ticket with impact, affected route/component, and user workaround.
2. Link the ticket in the PR under the accessibility exception checklist item.
3. Record an owner and target fix date.
4. Add a compensating mitigation (for example, alternate flow or support assist).
5. Remove the exception and close the ticket once fixed.

Exceptions are time-bound and must not be left without an owner.

## Remediation tracking

Track accessibility defects in a dedicated backlog label (for example, `accessibility`).
Each issue should include:

- WCAG criterion reference (for example, `1.3.1`, `2.1.1`, `4.1.2`)
- Severity (`critical`, `serious`, `moderate`, `minor`)
- Reproduction route and selector(s)
- Affected assistive technology scenario (keyboard-only, screen reader, etc.)
- SLA target date and accountable owner

## Acceptance criteria for keyboard and screen-reader support

All user-facing features should meet:

- Full keyboard operability for primary workflows with visible focus state.
- Logical tab order with no keyboard traps.
- Proper semantic landmarks and heading hierarchy.
- Form controls with programmatic labels.
- Dynamic status updates announced using `aria-live` or role-based equivalents.
- Non-decorative images include meaningful alternative text.
