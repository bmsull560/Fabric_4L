---
description: Roll up metrics across value trees and capabilities
---

# Metrics Aggregator Workflow

Use this workflow to aggregate and rollup metrics across capabilities, use cases, and value drivers.

## Parameters

- `scope`: CAPABILITY | USE_CASE | PERSONA | VALUE_DRIVER | FULL_GRAPH (required)
- `scope_id`: ID of the entity to aggregate from (optional, defaults to root)
- `metric_types`: List of metrics (ROI, COST_SAVINGS, TIME_SAVINGS, RISK_REDUCTION) (default: all)
- `aggregation_method`: SUM | AVERAGE | WEIGHTED_AVERAGE | MAX (default: SUM)
- `time_period`: ANNUAL | QUARTERLY | MONTHLY (default: ANNUAL)

## Steps

1. Identify scope and starting entity
2. Traverse related entities in the graph
3. Collect metrics at each node
4. Apply aggregation method
5. Calculate roll-up totals
6. Validate consistency

## Output

Aggregated metrics report:
- Total values by metric type
- Breakdown by entity level
- Confidence-weighted scores
- Trends over time (if historical data available)

## Example Use

"What's the total ROI across all manufacturing capabilities?"
