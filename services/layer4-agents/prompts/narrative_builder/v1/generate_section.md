---
prompt_id: narrative_builder.generate_section
version: v1
workflow_type: narrative_builder
model_task: narrative
requires_json: false
temperature: 0.3
max_tokens: 1000
---
Write the {{ section_type }} section for a business case document.

Context:
{{ context }}

Tone: {{ tone }}

Section-specific guidance:
- executive_summary: 2-3 paragraphs covering current situation, proposed solution, expected ROI, and recommendation.
- current_state: Describe current pain points, inefficiencies, and business impact.
- proposed_solution: Cover capabilities offered, implementation approach, and alignment with needs.
- roi_analysis: Cover investment required, expected returns, payback period, and risk-adjusted NPV.
- implementation: Outline phases, timeline, key milestones, and resource requirements.
- next_steps: List immediate actions, decision points, and timeline for approval.

Maximum {{ max_length }} words. Write only the section content — no headings, no preamble.
