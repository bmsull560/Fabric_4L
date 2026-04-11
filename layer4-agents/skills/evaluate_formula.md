---
name: evaluate-formula
description: Execute mathematical formulas from Value Drivers with variable substitution
---

# Formula Evaluator Workflow

Use this workflow to execute mathematical formulas from Value Drivers.

## Parameters

- `formula_id`: ValueDriver node ID (string, required)
- `variables`: Dictionary of variable names to numeric values (required)
- `scenario`: BASE | BEST | WORST - For sensitivity analysis (default: BASE)

## Steps

1. Retrieve formula from Value Driver node
2. Substitute provided variables
3. Execute calculation
4. Show intermediate steps
5. Return calculated value with unit

## Output

Calculation result:
- Final calculated value with unit
- Intermediate calculation steps
- Variable substitutions made
- Confidence score of result

## Example Use

"Calculate ROI given 5000 hours saved at $75/hour"
