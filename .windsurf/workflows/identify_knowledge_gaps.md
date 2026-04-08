---
description: Recognize missing information in the Knowledge Graph
---

# Knowledge Gap Identifier Workflow

Use this workflow to identify areas where the Knowledge Graph lacks sufficient information.

## Parameters

- `topic_area`: Subject area to analyze (string, required)
- `depth`: SURFACE | DEEP (default: SURFACE)
- `gap_types`: List (MISSING_ENTITIES, INCOMPLETE_RELATIONSHIPS, MISSING_EVIDENCE, OUTDATED_INFO) (default: all)

## Steps

1. Analyze the specified topic area
2. Identify missing entity types
3. Find incomplete relationship networks
4. Detect claims without evidence
5. Flag potentially outdated information
6. Prioritize gaps by business impact

## Output

Gap analysis report:
- List of identified knowledge gaps
- Severity/importance scoring
- Impact on downstream workflows
- Recommendations for gap filling
- Suggested sources to fill gaps

## Example Use

"What do we need to know about healthcare compliance that we're missing?"
