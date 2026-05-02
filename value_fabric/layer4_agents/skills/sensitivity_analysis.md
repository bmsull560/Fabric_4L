---
name: sensitivity_analysis
description: Performs sensitivity analysis on formulas by varying inputs
---

# Sensitivity Analysis

Perform sensitivity analysis on formulas to understand how input variations affect outputs.

## Parameters

- `base_formula`: string — Formula to analyze (required)
- `base_variables`: object — Base variable values (required)
- `variable_ranges`: object — Ranges for each variable {var: [min, max, steps]} (required)

## Steps

1. Calculate base case result
2. For each variable, vary across range and recalculate
3. Build tornado chart data showing impact ranking
4. Identify optimal variable values

## Output

Returns SensitivityAnalysisOutput with:
- `scenarios`: Array of scenario results
- `tornado_data`: Impact ranking for tornado chart
- `optimal_variables`: Best performing variable combination
