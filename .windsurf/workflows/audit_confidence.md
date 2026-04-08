---
description: Identify weak links and low-confidence assertions in the graph
---

# Confidence Auditor Workflow

Use this workflow to audit confidence scores and identify weak links in the Knowledge Graph.

## Parameters

- `min_confidence`: Threshold below which to flag (default: 0.7)
- `entity_types`: List of entity types to audit (optional, default: all)
- `relationship_types`: List of relationship types to check (optional, default: all)
- `scope`: FULL_GRAPH | SUBSET (default: FULL_GRAPH)

## Steps

1. Scan entities and relationships in scope
2. Filter by confidence threshold
3. Identify low-confidence assertions
4. Check for cascading confidence issues
5. Flag critical paths with weak links
6. Recommend evidence strengthening

## Output

Audit report with:
- List of low-confidence entities and relationships
- Impact assessment for critical paths
- Evidence gaps identified
- Recommendations for confidence improvement

## Example Use

"Find all claims with confidence below 0.7 that affect business case generation"
