---
prompt_id: roi_calculator.hypothesis_generation
version: v1
workflow_type: roi_calculator_generation
model_task: reasoning
requires_json: true
output_schema: RoiHypothesisOutput
temperature: 0.2
max_tokens: 2000
---

Given the following ROI calculation results for account "{{ account_name }}":

## Formula Outputs
{{ formula_outputs_json }}

## Value Drivers
{{ value_drivers_json }}

## Benchmarks Used
{{ benchmarks_json }}

Produce a structured value hypothesis. Return JSON matching this schema exactly:

```json
{
  "hypothesis": "<one-sentence value hypothesis for this account>",
  "confidence": <float 0.0-1.0>,
  "confidence_rationale": "<why this confidence level>",
  "key_drivers": [
    {
      "driver_name": "<name>",
      "calculated_value": "<value with units>",
      "explanation": "<why this driver matters for this account>"
    }
  ],
  "risks": [
    {
      "risk": "<risk description>",
      "severity": "low|medium|high"
    }
  ],
  "narrative_summary": "<2-3 sentence executive summary>",
  "evidence_refs": ["<data point or benchmark cited>"]
}
```
