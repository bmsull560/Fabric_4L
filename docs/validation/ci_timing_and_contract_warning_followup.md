# CI Timing and Platform-Contract Warning Follow-Up

This follow-up closes the next low-risk improvement loop after the targeted CI-efficiency pass. The implementation adds a lightweight timing-artifact utility and removes the remaining platform-contract false-positive warning without weakening the agent-return contract that the warning was intended to enforce.

## Delivered Changes

| Area | Change | Production-Readiness Value |
|---|---|---|
| CI timing artifacts | Added `scripts/ci/run_timed_ci_checks.py`, a dependency-free wrapper that runs named checks, records wall-clock duration, preserves optional stdout artifacts, and emits JSON plus Markdown timing summaries. | Provides measurable regression evidence for recurring CI checks without adding external services or heavyweight telemetry. |
| PR structural workflow | Prepared the timing wrapper for PR structural checks, but did not modify `.github/workflows/pr-checks.yml` in this commit because the current GitHub token cannot push workflow-file changes. | Keeps the push compliant while leaving a ready-to-adopt timing path for maintainers with workflow-write permission. |
| Platform-contract warning | Refined `scripts/ci/platform_contract_lint.py` so the `raw_dict_agent_return` warning applies only to matches inside `execute` functions. | Removes the prior `shared/security/config.py` false positive while continuing to flag raw dictionary returns from agent execution paths. |

## Validation Evidence

The local validation focused on behavior that does not require live services or external credentials. It verified syntax, contract-lint behavior, and timing artifact generation.

| Check | Result | Evidence |
|---|---:|---|
| Python syntax | PASS | `python3 -m py_compile scripts/ci/run_timed_ci_checks.py scripts/ci/platform_contract_lint.py` completed successfully. |
| Platform contract lint | PASS | `python3 scripts/ci/platform_contract_lint.py` reported `Results: 0 errors, 0 warnings.` |
| Timing wrapper | PASS | `run_timed_ci_checks.py` successfully produced `ci-timing-summary.json` and `ci-timing-summary.md` for representative checks. |
| Dependabot coverage smoke check | PASS | `python3 scripts/ci/check_dependabot_coverage.py` reported `dependabot coverage OK — 8 pip, 4 npm, 7 docker (19 total manifest locations covered)`. |

## Maintainer Workflow Adoption

The timing wrapper is intentionally simple. It records durations in seconds, return codes, stdout and stderr byte counts, command strings, and optional stdout artifact locations. Future workflow changes can add more checks by appending additional `--check 'name|stdout_path|command'` entries, but maintainers should avoid wrapping very long-running integration suites until the artifact volume and log behavior have been reviewed. Because this session cannot push workflow-file updates, maintainers with workflow-write permission should wire the wrapper into `.github/workflows/pr-checks.yml` in a follow-up PR.

## Remaining Follow-Up Opportunities

| Priority | Opportunity | Rationale |
|---|---|---|
| P1 | Trend CI timing across multiple workflow runs. | The current artifacts enable manual review; a later loop could compare against historical baselines if a durable artifact store is selected. |
| P1 | Add timing to selected security/governance jobs. | The structural job can adopt the wrapper first; governance and security checks may expose additional low-risk bottlenecks. |
| P2 | Consolidate file-walk skip logic across CI validators. | Several validators still maintain local skip/prune rules. A shared helper could reduce maintenance cost, but should be introduced only after tests cover each validator's discovery scope. |
