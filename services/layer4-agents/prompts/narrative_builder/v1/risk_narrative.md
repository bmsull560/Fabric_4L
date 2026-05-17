---
prompt_id: narrative_builder.risk_narrative
version: v1
workflow_type: narrative_builder
model_task: narrative
requires_json: true
output_schema: RiskNarrativeOutput
temperature: 0.2
max_tokens: 800
---

Write a risk and mitigation narrative for account "{{ account_name }}" based on the following signals and business case context.

## Risk Signals
{{ risk_signals_json }}

## Business Case Sections
{{ sections_json }}

For each identified risk:
- State the risk clearly
- Quantify the potential impact where evidence supports it
- Provide a concrete mitigation recommendation

Return JSON:

```json
{
  "risk_narrative": "<1-2 paragraph narrative>",
  "risks": [
    {
      "risk": "<description>",
      "impact": "<quantified or qualitative>",
      "mitigation": "<recommendation>",
      "severity": "high|medium|low"
    }
  ],
  "overall_risk_level": "high|medium|low",
  "confidence": <float 0.0-1.0>
}
```
