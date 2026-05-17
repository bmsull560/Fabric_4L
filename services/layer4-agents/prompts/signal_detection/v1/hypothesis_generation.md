---
prompt_id: signal_detection.hypothesis_generation
version: v1
workflow_type: signal_detection
model_task: reasoning
requires_json: true
output_schema: SignalHypothesisSet
temperature: 0.2
max_tokens: 3000
---

Generate value hypotheses from the following high-confidence signal clusters for account "{{ account_name }}":

## Classified Signals (confidence >= 0.6)
{{ high_confidence_signals_json }}

For each distinct signal cluster, generate one value hypothesis. Return JSON:

```json
{
  "hypotheses": [
    {
      "hypothesis_text": "<specific, testable value hypothesis>",
      "signal_cluster": ["<signal_id>"],
      "supporting_evidence": ["<entity or source ref>"],
      "confidence": <float 0.0-1.0>,
      "recommended_action": "<next step to validate or act>"
    }
  ]
}
```
