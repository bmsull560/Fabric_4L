---
prompt_id: signal_detection.narrative
version: v1
workflow_type: signal_detection
model_task: narrative
requires_json: true
output_schema: SignalNarrativeOutput
temperature: 0.3
max_tokens: 1000
---

Write a 1-paragraph signal summary for account "{{ account_name }}" based on the following analysis:

## Signal Hypotheses
{{ hypotheses_json }}

## Classified Signals Summary
{{ signal_summary_json }}

Return JSON:

```json
{
  "narrative": "<1-paragraph signal summary suitable for a sales rep briefing>",
  "top_signals": ["<top 3 signal descriptions>"],
  "evidence_refs": ["<key sources cited>"],
  "confidence": <float 0.0-1.0>
}
```
