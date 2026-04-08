---
description: Express confidence levels for generated outputs
---

# Uncertainty Quantifier Workflow

Use this workflow to calculate and express confidence levels for any generated output.

## Parameters

- `output_id`: ID of the generated output (string, required)
- `factors`: List of factors to consider (SOURCE_QUALITY, EVIDENCE_STRENGTH, MODEL_CONFIDENCE, DATA_COMPLETENESS) (default: all)
- `calculation_method`: SIMPLE_AVERAGE | WEIGHTED | BAYESIAN (default: WEIGHTED)

## Steps

1. Retrieve the generated output
2. Trace back to source materials
3. Assess each confidence factor
4. Calculate overall confidence score
5. Identify primary uncertainty drivers
6. Express confidence with explanation

## Output

Confidence assessment:
- Overall confidence score (0.0-1.0)
- Factor-by-factor breakdown
- Explanation of uncertainty drivers
- Recommendations to improve confidence
- Whether output meets confidence thresholds

## Example Use

"What's the confidence level for the $2.5M ROI calculation?"
