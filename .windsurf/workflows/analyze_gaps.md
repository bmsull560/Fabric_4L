---
description: Identify missing capabilities or disconnected value chains
---

# Gap Analysis Workflow

Use this workflow to identify gaps in capabilities or disconnected value chains.

## Parameters

- `context`: Prospect description or requirements (string, required)
- `comparison_scope`: FULL_GRAPH | SUBSET (provide node_ids) (default: FULL_GRAPH)
- `gap_types`: List of gap types (MISSING_CAPABILITY, DISCONNECTED_VALUE, UNMAPPED_PERSONA) (optional)

## Steps

1. Parse the prospect context/requirements
2. Compare against existing graph structure
3. Identify missing capabilities
4. Find disconnected value chains
5. Score gaps by severity
6. Provide recommendations

## Output

Gap analysis report:
- List of missing capabilities
- Disconnected value chains identified
- Severity scores per gap
- Recommendations to address gaps
- Potential impact of filling gaps

## Example Use

"What capabilities are we missing for healthcare prospects?"
