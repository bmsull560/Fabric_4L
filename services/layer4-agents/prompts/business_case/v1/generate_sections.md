---
prompt_id: business_case.generate_sections
version: v1
workflow_type: business_case_generation
model_task: narrative
requires_json: true
output_schema: BusinessCaseSections
temperature: 0.3
max_tokens: 5000
---

Generate the following business case section for account "{{ account_name }}":

## Section Type
{{ section_type }}

## Business Case Brief
{{ brief_json }}

## Additional Context
{{ section_context_json }}

Return JSON:

```json
{
  "section_type": "{{ section_type }}",
  "content": "<section prose>",
  "claims": [
    {
      "claim_text": "<specific factual claim>",
      "claim_type": "metric|benchmark|outcome|risk",
      "evidence_refs": ["<source>"],
      "confidence": <float 0.0-1.0>
    }
  ],
  "evidence_refs": ["<source used in this section>"],
  "confidence": <float 0.0-1.0>
}
```
