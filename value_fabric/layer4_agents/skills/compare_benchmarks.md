---
name: compare_benchmarks
description: Compares metrics against industry benchmarks
---

# Compare Benchmarks

Compare business metrics against industry benchmarks to assess relative performance.

## Parameters

- `metric_name`: string — Metric to compare (required)
- `value`: number — Your metric value (required)
- `industry`: string — Industry vertical (optional)
- `company_size`: string — Company size category (optional)
- `region`: string — Geographic region (optional)

## Steps

1. Lookup benchmark data for metric/industry/size combination
2. Calculate percentile ranking
3. Generate comparison text
4. Return confidence score

## Output

Returns CompareBenchmarksOutput with:
- `percentile`: Percentile ranking 0-100
- `industry_average`: Benchmark average value
- `comparison_text`: Human-readable comparison
- `confidence`: Confidence level 0.0-1.0
