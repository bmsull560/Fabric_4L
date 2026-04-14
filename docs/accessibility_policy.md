# Value Fabric Accessibility Policy

## Policy Scope

This policy applies to all user-facing web experiences in `frontend/`, including authenticated product surfaces and login flows.

## Accessibility Target

- **Conformance target:** WCAG **2.2 Level AA** for all new features and material UI updates.
- **Release gate:** No unresolved **critical** automated accessibility violations are permitted in CI.
- **Design baseline:** Interactive controls must support keyboard-only operation, visible focus indicators, and sufficient semantic labeling.

## Supported Assistive Technology Matrix

The team validates core journeys against this support matrix:

| Platform | Browser | Screen Reader / AT |
|----------|---------|--------------------|
| Windows 11 | Chrome (latest stable) | NVDA (latest stable) |
| Windows 11 | Edge (latest stable) | JAWS (latest stable) |
| macOS (current -1) | Safari (latest stable) | VoiceOver (built-in) |
| iOS (current -1) | Safari (latest stable) | VoiceOver (built-in) |
| Android (current -1) | Chrome (latest stable) | TalkBack (built-in) |

## Testing Cadence

### Per Pull Request

- Run automated axe-based scans in frontend CI.
- CI fails when a **critical** violation is detected.

### Weekly

- Execute a curated manual accessibility smoke test:
  - keyboard navigation through primary nav and forms,
  - focus order verification,
  - color contrast checks on key screens,
  - screen reader spot-check of login and dashboard flows.

### Pre-Release

- Complete full accessibility checklist for changed user journeys.
- Verify documented exceptions and create remediation tickets for non-blocking issues.

## Exception Handling

- Accessibility exceptions require:
  1. documented issue with impacted users and workaround,
  2. severity and business impact,
  3. committed remediation owner and due date.

## Ownership

- **Primary owner:** Frontend Engineering.
- **Review partners:** Product Design and QA.
- **Escalation path:** Accessibility findings that block user completion of primary journeys are treated as release blockers.
