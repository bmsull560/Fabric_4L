---
description: Run Monte Carlo simulation on formula variables
---

# Sensitivity Analyzer Workflow

Use this workflow to run Monte Carlo simulations for sensitivity analysis.

## Parameters

- `formula_id`: Formula identifier (string, required)
- `variable_distributions`: Dictionary mapping variables to distributions
- `iterations`: Integer (default: 1000)
- `confidence_intervals`: List of confidence levels (default: [0.5, 0.9])

## Steps

1. Retrieve formula structure
2. Set up variable distributions
3. Run Monte Carlo simulation
4. Calculate distribution statistics
5. Compute p10/p50/p90 values
6. Provide risk assessment

## Output

Sensitivity analysis report:
- p10/p50/p90 percentile values
- Distribution statistics (mean, std dev)
- Confidence intervals
- Risk assessment summary
- Key variable impact rankings

## Example Use

"What's the range of possible ROI outcomes?"
