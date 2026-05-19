---
prompt_id: business_case.validate_claims
version: v1
workflow_type: business_case_generation
model_task: extraction
requires_json: true
output_schema: ClaimExtractionOutput
temperature: 0.0
max_tokens: 3000
---

Extract all factual claims from the following business case sections for account "{{ account_name }}":

## Sections
{{ sections_json }}

For each claim, assess whether it is:
- `validated`: supported by cited evidence in the input
- `needs_review`: asserted but evidence is weak or missing
- `insufficient_evidence`: no supporting evidence found

Return JSON:

```json
{
  "claims": [
    {
      "claim_id": "<unique id>",
      "claim_text": "<exact claim>",
      "source_section": "<section_type>",
      "validation_status": "validated|needs_review|insufficient_evidence",
      "evidence_refs": ["<source>"],
      "confidence": <float 0.0-1.0>
    }
  ]
}
```
