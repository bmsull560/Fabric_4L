---
description: Search web for additional context not in Knowledge Graph
---

# Web Researcher Workflow

Use this workflow to search the web for additional context beyond the Knowledge Graph.

## Parameters

- `query`: Search query (string, required)
- `sources`: List of source types (NEWS, FINANCIAL, COMPANY_WEBSITE, INDUSTRY_REPORTS)
- `max_results`: Integer (default: 5)
- `recency_days`: Integer - How recent results should be

## Steps

1. Formulate search query
2. Execute searches across specified sources
3. Filter by recency requirements
4. Summarize findings
5. Include source URLs

## Output

Research findings:
- Summarized information from sources
- Source URLs with access dates
- Key quotes and excerpts
- Source reliability indicators
- Confidence assessment per finding

## Example Use

"What are Target Corp's stated strategic priorities for 2024?"
