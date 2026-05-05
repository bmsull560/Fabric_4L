# Final-Testing Launch Gate Design

This document defines the launch-blocker taxonomy and the repository-owned checks that can be completed before final testing. It intentionally separates **repo-verifiable launch readiness** from **environment-dependent production evidence** so the team can move into final testing with a disciplined go/no-go posture without claiming live production readiness prematurely.

## Launch-Blocker Taxonomy

| Severity | Definition | Examples | Merge/Sign-Off Rule |
|---|---|---|---|
| P0 Launch Blocker | A defect or missing control that can cause data loss, security exposure, complete workflow failure, inability to roll back, or inability to observe production incidents. | Authentication fails open, tenant data leakage, critical workflow cannot complete, secrets committed to source, rollback not documented, live health gate fails. | Must be fixed, mitigated with executive approval, or explicitly removed from launch scope before final testing sign-off. |
| P1 Launch Blocker | A high-impact issue that can materially degrade launch quality, reliability, supportability, or compliance but has a bounded workaround. | Alert routing incomplete, non-critical workflow persistence missing, incomplete rate-limit evidence, unowned incident runbook. | Must have an owner, mitigation, validation plan, and launch decision before sign-off. |
| P2 Follow-Up | A known readiness gap that is not expected to block launch if monitored and scheduled. | SDK polish, long-term timing trend dashboards, post-launch compliance evidence packaging. | Must be tracked with an owner and target date, but does not block final testing. |
| Informational | Documentation, cleanup, or future-hardening task with no direct launch risk. | Duplicate docs, refactor opportunities, optional workflow wiring blocked by repository permissions. | Does not block final testing. |

## Repo-Owned Final-Testing Gate

The automated repository-level gate should answer whether the codebase is structurally ready to enter final testing. It does not replace live end-to-end testing. The gate should fail on unsafe repository state, missing launch-signoff documents, missing production-readiness foundations, unredacted secret-like values in owned launch artifacts, or known contract-lint failures.

| Gate Area | Automated Check | Expected Result |
|---|---|---|
| Launch documents | Required launch checklist, blocker register, go/no-go template, and environment evidence matrix exist. | PASS when required files are present and contain explicit P0/P1/P2 classifications. |
| Production-readiness foundations | Existing `validate_production_readiness_plan.py` passes. | PASS when policy JSON, runbooks, and repo evidence remain present. |
| Platform contracts | `platform_contract_lint.py` passes with zero errors and zero warnings. | PASS when agent-return and platform-boundary contracts remain clean. |
| Dependabot coverage | `check_dependabot_coverage.py` passes. | PASS when dependency manifest locations remain covered. |
| Security artifact hygiene | Launch docs and production-readiness config do not contain obvious raw secrets, bearer tokens, private keys, or unredacted provider credentials. | PASS when only placeholder, external-secret-reference, or redacted values are present. |
| Environment-dependent gate separation | Final-testing matrix marks live-stack, SSO, notification, telemetry, billing, rollback, and performance evidence as `REQUIRES_ENVIRONMENT` unless real evidence is attached. | PASS when the repo does not overclaim production PASS. |

## Implementation Approach

The implementation should add a small dependency-free validator under `scripts/ci/validate_final_testing_launch_gate.py`. The validator should reuse existing scripts rather than duplicate their business logic, scan only bounded launch-readiness paths for unsafe secret patterns, and emit concise pass/fail output suitable for local execution or later CI workflow wiring. A companion document set should include the launch checklist, blocker register template, and environment evidence matrix so final-testing owners know exactly which items remain outside this sandbox's technical resources.
