#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

DASHBOARD = Path("monitoring/grafana/dashboards/layer6-benchmarks.json")
CONTRACT = Path("contracts/observability/layer6-metrics.json")
PROMQL_METRIC = re.compile(r"\b([a-zA-Z_:][a-zA-Z0-9_:]*)\b")


def extract_metric_tokens(expr: str) -> set[str]:
    return {token for token in PROMQL_METRIC.findall(expr) if token.startswith("layer6_")}


def main() -> int:
    expected = {m["name"] for m in json.loads(CONTRACT.read_text())["metrics"]}
    dashboard = json.loads(DASHBOARD.read_text())
    stale: set[str] = set()
    for panel in dashboard.get("panels", []):
        for target in panel.get("targets", []):
            for metric in extract_metric_tokens(target.get("expr", "")):
                if metric not in expected:
                    stale.add(metric)
    if stale:
        print("Stale Layer 6 metric references found:")
        for metric in sorted(stale):
            print(f" - {metric}")
        return 1
    print("Layer 6 dashboard metric references match emitted metric names.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
