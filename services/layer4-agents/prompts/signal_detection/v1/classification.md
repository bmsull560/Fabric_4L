---
prompt_id: signal_detection.classification
version: v1
workflow_type: signal_detection
model_task: extraction
requires_json: true
output_schema: SignalClassificationOutput
temperature: 0.0
max_tokens: 3000
---

Classify the following signals extracted from account "{{ account_name }}":

## Extracted Signals
{{ signals_json }}

## Entities and Relationships
{{ entities_json }}

For each signal, assign a category and confidence score. Return JSON:

```json
{
  "classified_signals": [
    {
      "signal_id": "<id from input>",
      "signal_text": "<signal description>",
      "category": "pain|initiative|budget_signal|stakeholder_signal|risk|opportunity",
      "confidence": <float 0.0-1.0>,
      "evidence_refs": ["<entity or source ref>"]
    }
  ]
}
```
