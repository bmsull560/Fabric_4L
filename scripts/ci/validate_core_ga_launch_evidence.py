#!/usr/bin/env python3
"""Guard Core GA launch evidence claims.

This check is deliberately conservative. Missing live or CI evidence is allowed only when the
launch docs keep it explicitly open or environment-dependent. The script must not fabricate
evidence, infer production readiness from local deterministic tests, or treat paid GA as ready
without billing evidence.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FOLLOW_UP = ROOT / "docs/launch/core-ga-launch-readiness-follow-up.md"
BLOCKER_REGISTER = ROOT / "docs/launch/launch-blocker-register.md"
FINAL_SIGN_OFF = ROOT / "docs/validation/launch_readiness_final_sign_off_evidence.md"


@dataclass(frozen=True)
class EvidenceRequirement:
    name: str
    artifact_tokens: tuple[str, ...]
    open_tokens: tuple[str, ...]
    required_docs_tokens: tuple[str, ...] = ()
    local_paths: tuple[str, ...] = ()


REQUIREMENTS: tuple[EvidenceRequirement, ...] = (
    EvidenceRequirement(
        name="full_frontend_test_report",
        artifact_tokens=("frontend-test-report", "full frontend test report"),
        open_tokens=("P1-006", "Full frontend test report", "OPEN", "pnpm --dir apps/web run test"),
    ),
    EvidenceRequirement(
        name="security_suite_report",
        artifact_tokens=("security-suite-report", "security suite report"),
        open_tokens=("P1-007", "Broad security suite report", "OPEN", "pytest tests/security"),
    ),
    EvidenceRequirement(
        name="journey_slo_report",
        artifact_tokens=("journey-slo-report.json", "JOURNEY_SLO_REPORT_PATH"),
        open_tokens=("P1-008", "Journey SLO report", "OPEN", "test:journey-slo-gate"),
        local_paths=("apps/web/tmp/journey-slo-report.json",),
    ),
    EvidenceRequirement(
        name="live_llm_provider_evidence",
        artifact_tokens=("live-llm-provider-evidence", "Live LLM provider validation"),
        open_tokens=("P1-009", "Live LLM provider validation", "REQUIRES_ENVIRONMENT"),
    ),
    EvidenceRequirement(
        name="sso_oidc_evidence",
        artifact_tokens=("sso-oidc-evidence", "SSO/OIDC validation evidence"),
        open_tokens=("P0-003", "Enterprise SSO/OIDC provider validation", "REQUIRES_ENVIRONMENT"),
    ),
    EvidenceRequirement(
        name="billing_evidence",
        artifact_tokens=("billing-evidence", "Billing validation evidence"),
        open_tokens=("P1-003", "Billing and metering provider validation", "REQUIRES_ENVIRONMENT"),
        required_docs_tokens=("Paid GA remains blocked",),
    ),
    EvidenceRequirement(
        name="rollback_restore_evidence",
        artifact_tokens=("rollback-restore-evidence", "Rollback/restore transcript"),
        open_tokens=("P0-002", "Rollback and restore drill", "REQUIRES_ENVIRONMENT"),
    ),
    EvidenceRequirement(
        name="telemetry_alerting_evidence",
        artifact_tokens=("telemetry-alerting-evidence", "Telemetry dashboard and alert evidence"),
        open_tokens=("P1-002", "Telemetry dashboard", "REQUIRES_ENVIRONMENT"),
    ),
    EvidenceRequirement(
        name="alert_receiver_evidence",
        artifact_tokens=("alert-receiver-evidence", "Alert receiver"),
        open_tokens=("P1-001", "Notification and alert receiver validation", "REQUIRES_ENVIRONMENT"),
    ),
    EvidenceRequirement(
        name="performance_smoke_artifact",
        artifact_tokens=("performance-smoke-artifact", "Performance smoke artifact"),
        open_tokens=("P1-004", "Performance and reliability smoke test", "REQUIRES_ENVIRONMENT"),
    ),
)

PRODUCTION_READY_CLAIMS = (
    re.compile(r"\bproduction readiness (?:is )?(?:complete|proven|passed)\b", re.IGNORECASE),
    re.compile(r"\blive production readiness (?:is )?(?:complete|proven|passed)\b", re.IGNORECASE),
    re.compile(r"\bpaid ga (?:is )?(?:ready|approved|unblocked)\b", re.IGNORECASE),
    re.compile(r"\bcore ga (?:is )?production-ready\b", re.IGNORECASE),
)

NEGATION_HINTS = (
    "not ",
    "not yet",
    "does not",
    "cannot",
    "unproven",
    "requires_environment",
    "blocked",
    "remains open",
    "remains environment-dependent",
)

J1_DEEP_EXCEPTION_POLICY_TOKENS = (
    "## j1 deep secondary-coverage exception process",
    "j1-golden-path-deep.spec.ts",
    "pnpm --dir apps/web run test:e2e:golden:j1:deep",
    "failure summary",
    "root cause category",
    "why non-blocking for production readiness",
    "risk level",
    "owner",
    "target remediation date",
    "link to issue/pr",
    "evidence j1 backend-integrated canonical p0 still passes",
    "evidence j11 parallel regression still passes",
    "code-owner approval acknowledgment",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def contains_all(text: str, tokens: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return all(token.lower() in lowered for token in tokens)


def local_artifact_exists(requirement: EvidenceRequirement) -> bool:
    return any((ROOT / relative).exists() for relative in requirement.local_paths)


def has_artifact_reference(combined_docs: str, requirement: EvidenceRequirement) -> bool:
    return any(token.lower() in combined_docs.lower() for token in requirement.artifact_tokens)


def is_tracked_open(register_text: str, requirement: EvidenceRequirement) -> bool:
    return contains_all(register_text, requirement.open_tokens)


def suspicious_positive_claims(text: str) -> list[str]:
    findings: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        if any(hint in lowered for hint in NEGATION_HINTS):
            continue
        for pattern in PRODUCTION_READY_CLAIMS:
            if pattern.search(line):
                findings.append(f"line {line_number}: {line.strip()}")
                break
    return findings


def main() -> int:
    failures: list[str] = []

    required_paths = (FOLLOW_UP, BLOCKER_REGISTER, FINAL_SIGN_OFF)
    for path in required_paths:
        if not path.exists():
            failures.append(f"missing required launch document: {path.relative_to(ROOT)}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    follow_up = read_text(FOLLOW_UP)
    register = read_text(BLOCKER_REGISTER)
    final_sign_off = read_text(FINAL_SIGN_OFF)
    combined_docs = "\n".join((follow_up, register, final_sign_off))

    for requirement in REQUIREMENTS:
        artifact_present = local_artifact_exists(requirement)
        artifact_referenced = has_artifact_reference(combined_docs, requirement)
        tracked_open = is_tracked_open(register, requirement)

        if artifact_present and not artifact_referenced:
            failures.append(
                f"{requirement.name}: artifact exists but is not referenced in launch docs"
            )
        if not artifact_present and not tracked_open:
            failures.append(
                f"{requirement.name}: missing artifact must remain explicitly OPEN or REQUIRES_ENVIRONMENT "
                "in docs/launch/launch-blocker-register.md"
            )
        for token in requirement.required_docs_tokens:
            if token.lower() not in combined_docs.lower():
                failures.append(f"{requirement.name}: required launch guard text missing: {token!r}")

    register_lower = register.lower()
    missing_j1_policy = [
        token for token in J1_DEEP_EXCEPTION_POLICY_TOKENS if token not in register_lower
    ]
    if missing_j1_policy:
        failures.append(
            "j1_deep_exception_policy: launch-blocker register is missing required "
            "J1 deep waiver policy tokens: "
            + ", ".join(missing_j1_policy)
        )

    if not local_artifact_exists(REQUIREMENTS[2]) and "journey-slo-report.json" not in combined_docs:
        failures.append("journey_slo_report: missing SLO file must be named in launch docs")

    positive_claims = suspicious_positive_claims(final_sign_off)
    if positive_claims:
        failures.append(
            "final sign-off evidence doc appears to claim production readiness without evidence: "
            + " ; ".join(positive_claims[:5])
        )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("Core GA launch evidence guard OK: missing evidence remains explicitly open or environment-dependent.")
    print("NOTE: Paid GA remains blocked unless billing evidence passes or paid launch is removed from scope.")
    print("NOTE: Production readiness is not proven by local deterministic-path evidence alone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
