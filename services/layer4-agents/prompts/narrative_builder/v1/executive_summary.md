---
prompt_id: narrative_builder.executive_summary
version: v1
workflow_type: narrative_builder
model_task: narrative
requires_json: true
output_schema: ExecutiveSummaryOutput
temperature: 0.3
max_tokens: 800
---

Write a 3–5 sentence executive summary for the following business case.

## Account
{{ account_name }}

## Business Case Sections
{{ sections_json }}

## Validated Claims
{{ validated_claims_json }}

## ROI Summary
{{ roi_summary_json }}

The summary must:
- Open with the primary value proposition in one sentence
- State the top 2–3 quantified outcomes (use validated figures only)
- Close with the recommended next step

Return JSON:

```json
{
  "executive_summary": "<3-5 sentence summary>",
  "primary_value_proposition": "<one sentence>",
  "top_outcomes": ["<outcome 1>", "<outcome 2>", "<outcome 3>"],
  "recommended_next_step": "<one sentence>",
  "confidence": <float 0.0-1.0>
}
```
