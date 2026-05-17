---
prompt_id: narrative_builder.value_narrative
version: v1
workflow_type: narrative_builder
model_task: narrative
requires_json: true
output_schema: ValueNarrativeOutput
temperature: 0.3
max_tokens: 1200
---

Write a value narrative section for account "{{ account_name }}" based on the following inputs.

## ROI Hypotheses
{{ roi_hypotheses_json }}

## Whitespace Opportunities
{{ whitespace_opportunities_json }}

## Validated Claims
{{ validated_claims_json }}

Write 2–4 paragraphs covering:
1. The primary business problem and its cost
2. How the solution addresses it with quantified outcomes
3. Expansion opportunities identified in whitespace analysis

Return JSON:

```json
{
  "value_narrative": "<2-4 paragraph narrative>",
  "primary_problem": "<one sentence>",
  "quantified_outcomes": [
    {
      "outcome": "<description>",
      "value": "<metric or range>",
      "evidence_ref": "<source>"
    }
  ],
  "expansion_opportunities": ["<opportunity 1>", "<opportunity 2>"],
  "confidence": <float 0.0-1.0>
}
```
