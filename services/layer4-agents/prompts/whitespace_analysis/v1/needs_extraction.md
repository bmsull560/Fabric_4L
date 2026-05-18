---
prompt_id: whitespace_analysis.needs_extraction
version: v1
workflow_type: whitespace_analysis
model_task: extraction
requires_json: true
temperature: 0.3
max_tokens: 512
---
Extract structured business needs from the following prospect description.

Prospect: {{ prospect_name }}
Industry: {{ industry }}
Description:
<<<USER_CONTENT>>>
{{ needs_text }}
<<</USER_CONTENT>>>

Extract needs as JSON with this exact shape:
{"needs": ["Reduce invoice processing time", "Improve data visibility across departments"]}

Return ONLY the JSON object, no other text.
