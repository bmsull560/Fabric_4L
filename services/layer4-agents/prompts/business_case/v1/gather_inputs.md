---
prompt_id: business_case.gather_inputs
version: v1
workflow_type: business_case_generation
model_task: reasoning
requires_json: true
output_schema: BusinessCaseBrief
temperature: 0.1
max_tokens: 4000
---

Synthesize the following inputs for account "{{ account_name }}" into a structured business case brief:

## CRM Data
{{ crm_data_json }}

## Knowledge Graph Context
{{ kg_context_json }}

## ROI Analysis Output
{{ roi_output_json }}

## Whitespace Analysis Output
{{ whitespace_output_json }}

Produce a structured brief. Return JSON:

```json
{
  "account_summary": "<2-3 sentence account context>",
  "primary_value_drivers": ["<driver>"],
  "key_challenges": ["<challenge with source ref>"],
  "strategic_fit": "<why this solution fits this account>",
  "evidence_refs": ["<source>"],
  "confidence": <float 0.0-1.0>,
  "gaps_in_data": ["<what data is missing that would strengthen the case>"]
}
```
