---
description: Find contradictory information in the Knowledge Graph
---

# Conflict Detector Workflow

Use this workflow to identify contradictory or inconsistent information in the Knowledge Graph.

## Parameters

- `scope`: FULL_GRAPH | ENTITY_SUBSET (default: FULL_GRAPH)
- `entity_ids`: List of entity IDs to check (required if scope=ENTITY_SUBSET)
- `confidence_threshold`: Minimum confidence to flag (default: 0.8)
- `check_types`: List of checks (CONTRADICTORY_CLAIMS, DUPLICATE_ENTITIES, ORPHANED_NODES, BROKEN_RELATIONSHIPS)

## Steps

1. Scan specified scope for potential conflicts
2. Identify contradictory claims about entities
3. Detect duplicate or near-duplicate entities
4. Find orphaned nodes (no relationships)
5. Check for broken relationship references
6. Score conflicts by severity
7. Recommend resolutions

## Output

Conflict report containing:
- List of identified conflicts with severity scores
- Conflicting statements or entity details
- Recommended resolution actions
- Confidence scores for each finding

## Example Use

"Are there any contradictory claims about our ROI calculations?"
