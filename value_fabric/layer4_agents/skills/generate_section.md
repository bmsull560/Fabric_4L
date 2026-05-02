---
name: generate_section
description: Generates narrative sections for business cases using LLM
---

# Generate Section

Generate narrative sections for business cases using LLM-powered content generation.

## Parameters

- `section_type`: string — Type: executive_summary, current_state, proposed_solution, roi_analysis, implementation, next_steps (required)
- `context`: object — Key-value context data (optional)
- `tone`: string — Writing tone (default: professional)
- `max_length`: integer — Maximum word count 100-2000 (default: 500)

## Steps

1. Select template for section type
2. Build prompt with context and tone
3. Call LLM with budget guardrails
4. Extract and structure content
5. Return with metadata

## Output

Returns GenerateSectionOutput with:
- `content`: Generated text content
- `word_count`: Actual word count
- `key_points`: Extracted key points
