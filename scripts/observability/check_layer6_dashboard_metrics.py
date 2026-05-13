#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

CONTRACT = Path("contracts/observability/layer6-metrics.json")
DASHBOARD_DIR = Path("monitoring/grafana/dashboards")
ALERT_RULES = (Path("monitoring/alerting/rules.yml"),)
PROMQL_METRIC = re.compile(r"\b([a-zA-Z_:][a-zA-Z0-9_:]*)\b")


def extract_metric_tokens(expr: str) -> set[str]:
    return {token for token in PROMQL_METRIC.findall(expr) if token.startswith("layer6_")}


def iter_dashboard_expressions(payload: object):
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key == "expr" and isinstance(value, str):
                yield value
            else:
                yield from iter_dashboard_expressions(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from iter_dashboard_expressions(item)


def main() -> int:
    expected = {m["name"] for m in json.loads(CONTRACT.read_text(encoding="utf-8"))["metrics"]}
    expected_tokens = set(expected)
    for metric_name in expected:
        if metric_name.endswith("_seconds"):
            expected_tokens.update(
                {
                    f"{metric_name}_bucket",
                    f"{metric_name}_sum",
                    f"{metric_name}_count",
                }
            )
    stale: dict[str, set[str]] = {}

    for dashboard in DASHBOARD_DIR.glob("*.json"):
        payload = json.loads(dashboard.read_text(encoding="utf-8"))
        referenced = set().union(
            *(extract_metric_tokens(expr) for expr in iter_dashboard_expressions(payload))
        )
        unknown = referenced - expected_tokens
        if unknown:
            stale[str(dashboard)] = unknown

    for rules_file in ALERT_RULES:
        referenced = extract_metric_tokens(rules_file.read_text(encoding="utf-8"))
        unknown = referenced - expected_tokens
        if unknown:
            stale[str(rules_file)] = unknown

    if stale:
        print("Stale Layer 6 metric references found:")
        for path, names in sorted(stale.items()):
            print(f"{path}:")
            for name in sorted(names):
                print(f"  - {name}")
        return 1

    print("Layer 6 dashboard and alert metric references match emitted metric names.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
