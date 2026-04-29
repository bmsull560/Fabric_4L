#!/usr/bin/env python3
"""Evaluate k6 summary output against versioned SLO targets.

Exits with code 1 when SLO breaches or regressions are detected.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from math import isfinite
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class BurnRateWindow:
    window: str
    threshold: float
    observed: float
    status: str


@dataclass
class TargetResult:
    service: str
    api: str
    latency_metric: str
    measured_p95_ms: float
    latency_target_ms: float
    latency_regression_limit_ms: float
    latency_status: str
    error_metric: str
    measured_error_rate: float
    error_target_rate: float
    error_regression_limit_rate: float
    error_status: str
    runbook: str
    incident_template: str
    burn_rate_windows: list[BurnRateWindow]

    @property
    def passed(self) -> bool:
        return self.latency_status == "pass" and self.error_status == "pass"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _get_metric(summary: dict[str, Any], metric_name: str) -> dict[str, Any]:
    metrics = summary.get("metrics", {})
    if metric_name not in metrics:
        raise KeyError(f"Metric '{metric_name}' not found in k6 summary")
    return metrics[metric_name]


def evaluate(summary: dict[str, Any], slo: dict[str, Any]) -> list[TargetResult]:
    policy = slo.get("regression_policy", {})
    latency_regression_pct = float(policy.get("latency_regression_pct", 0.0))
    error_regression_abs = float(policy.get("error_rate_regression_abs", 0.0))

    results: list[TargetResult] = []
    for target in slo.get("targets", []):
        latency_metric = target["metric"]
        error_metric = target["error_metric"]

        latency_values = _get_metric(summary, latency_metric).get("values", {})
        error_values = _get_metric(summary, error_metric).get("values", {})

        measured_p95 = float(latency_values.get("p(95)", 0.0))
        measured_error = float(error_values.get("rate", 0.0))

        latency_target = float(target["objective"]["max"])
        error_target = float(target["error_objective"]["max"])

        latency_regression_limit = latency_target * (1.0 + latency_regression_pct)
        error_regression_limit = error_target + error_regression_abs

        latency_status = "pass" if measured_p95 <= latency_regression_limit else "fail"
        error_status = "pass" if measured_error <= error_regression_limit else "fail"

        breach = target.get("breach_response", {})

        error_budget_fraction = 1.0 - float(target.get("availability_slo", 0.99))
        burn_policy = target.get("burn_rate_policy", {})
        windows: list[BurnRateWindow] = []
        if error_budget_fraction > 0 and isfinite(error_budget_fraction):
            observed_burn_rate = measured_error / error_budget_fraction
            for policy_window in burn_policy.get("windows", []):
                threshold = float(policy_window.get("threshold", 0.0))
                status = "pass" if observed_burn_rate <= threshold else "fail"
                windows.append(
                    BurnRateWindow(
                        window=str(policy_window.get("window", "unknown")),
                        threshold=threshold,
                        observed=observed_burn_rate,
                        status=status,
                    )
                )

        results.append(
            TargetResult(
                service=target["service"],
                api=target["api"],
                latency_metric=latency_metric,
                measured_p95_ms=measured_p95,
                latency_target_ms=latency_target,
                latency_regression_limit_ms=latency_regression_limit,
                latency_status=latency_status,
                error_metric=error_metric,
                measured_error_rate=measured_error,
                error_target_rate=error_target,
                error_regression_limit_rate=error_regression_limit,
                error_status=error_status,
                runbook=breach.get("runbook", ""),
                incident_template=breach.get("incident_template", ""),
                burn_rate_windows=windows,
            )
        )

    return results


def render_markdown(results: list[TargetResult], generated_at: str) -> str:
    lines = [
        "# Performance SLO Evaluation",
        "",
        f"Generated at: **{generated_at}**",
        "",
        "| Service | API | p95 ms | Limit ms | Error rate | Limit | Status |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]

    for result in results:
        burn_fail = any(w.status == "fail" for w in result.burn_rate_windows)
        status = "✅ pass" if result.passed and not burn_fail else "❌ breach"
        lines.append(
            "| {service} | `{api}` | {p95:.2f} | {p95_limit:.2f} | {err:.4f} | {err_limit:.4f} | {status} |".format(
                service=result.service,
                api=result.api,
                p95=result.measured_p95_ms,
                p95_limit=result.latency_regression_limit_ms,
                err=result.measured_error_rate,
                err_limit=result.error_regression_limit_rate,
                status=status,
            )
        )

    lines.extend(["", "## Breach runbook linkage", ""])
    for result in results:
        burn_fail = any(w.status == "fail" for w in result.burn_rate_windows)
        if result.passed and not burn_fail:
            continue
        lines.append(f"- **{result.service}**: follow `{result.runbook}` and create incident using `{result.incident_template}`.")
        for window in result.burn_rate_windows:
            if window.status == "fail":
                lines.append(f"  - Burn-rate breach `{window.window}`: observed {window.observed:.2f}x > threshold {window.threshold:.2f}x")

    if all(r.passed and all(w.status == "pass" for w in r.burn_rate_windows) for r in results):
        lines.append("- No breaches detected.")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate k6 performance results against SLO policy")
    parser.add_argument("--summary", required=True, help="Path to k6 --summary-export JSON")
    parser.add_argument("--slo", required=True, help="Path to versioned SLO definition JSON")
    parser.add_argument("--report", required=True, help="Path to output markdown report")
    parser.add_argument("--output", required=True, help="Path to output machine-readable evaluation JSON")
    args = parser.parse_args()

    summary_path = Path(args.summary)
    slo_path = Path(args.slo)
    report_path = Path(args.report)
    output_path = Path(args.output)

    summary = _read_json(summary_path)
    slo = _read_json(slo_path)

    generated_at = datetime.now(timezone.utc).isoformat()
    results = evaluate(summary, slo)

    all_passed = all(
        result.passed and all(window.status == "pass" for window in result.burn_rate_windows)
        for result in results
    )

    payload = {
        "generated_at": generated_at,
        "slo_version": slo.get("version"),
        "all_passed": all_passed,
        "results": [
            {
                **result.__dict__,
                "burn_rate_windows": [window.__dict__ for window in result.burn_rate_windows],
            }
            for result in results
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(render_markdown(results, generated_at), encoding="utf-8")

    print(report_path.read_text(encoding="utf-8"))
    return 0 if payload["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
