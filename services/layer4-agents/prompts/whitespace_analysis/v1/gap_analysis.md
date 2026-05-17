---
prompt_id: whitespace_analysis.gap_analysis
version: v1
workflow_type: whitespace_analysis
model_task: reasoning
requires_json: true
output_schema: GapAnalysisOutput
temperature: 0.1
max_tokens: 4000
---

Synthesize the following gap analysis for account "{{ account_name }}":

## Identified Needs
{{ needs_json }}

## Semantic Search Results
{{ search_results_json }}

## Existing Coverage
{{ existing_coverage_json }}

Produce a ranked gap analysis. Return JSON matching this schema exactly:

```json
{
  "gaps": [
    {
      "gap_description": "<what is unmet>",
      "rank": <integer starting at 1>,
      "confidence": <float 0.0-1.0>,
      "evidence_refs": ["<source>"],
      "opportunity_size": "small|medium|large|unknown"
    }
  ],
  "synthesis_note": "<brief note on overall gap landscape>"
}
```
