---
name: evaluate_formula
description: Evaluates a mathematical or business formula with variable substitution
---

# Evaluate Formula

Evaluates formulas using the FormulaEvaluationService.

## Parameters

- `formula_id`: UUID of the formula to evaluate
- `variable_values`: Dictionary of variable name to numeric value mappings
- `context`: Optional evaluation context (tenant_id, user_id, timestamp)

## Output

Returns evaluated result with computed value, unit, confidence score, and any validation warnings.
