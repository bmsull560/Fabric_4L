---
description: Find shortest or strongest path between two entities
---

# Path Finder Workflow

Use this workflow to find the path between two entities in the Knowledge Graph.

## Parameters

- `source_id`: Starting entity ID (string, required)
- `target_id`: Target entity ID (string, required)
- `algorithm`: SHORTEST | STRONGEST | ALL (default: SHORTEST)
- `max_hops`: Integer (default: 5)

## Steps

1. Identify source and target entities
2. Execute pathfinding algorithm
3. Calculate path strength/confidence
4. Return paths with confidence scores and evidence

## Output

List of paths with:
- Path sequence (node → relationship → node)
- Path strength/confidence score
- Evidence citations per relationship
- Alternative routes (if ALL algorithm selected)

## Example Use

"How does Real-Time Ingestion contribute to Cost Reduction?"
