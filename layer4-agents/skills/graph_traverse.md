---
name: graph-traverse
description: Navigate the Knowledge Graph via relationships to find connected entities
---

# Graph Traversal Workflow

Use this workflow to navigate the Knowledge Graph and find connected entities.

## Parameters

- `start_node_id`: Entity to start from (string, required)
- `relationship_types`: List of relationship types to follow (e.g., ENABLES, BENEFITS, DRIVES, CONTRIBUTES_TO)
- `direction`: OUTGOING | INCOMING | BOTH (default: BOTH)
- `depth`: Integer 1-5 (default: 2)
- `min_confidence`: Float 0.0-1.0 - Filter by relationship confidence

## Steps

1. Identify the starting entity node
2. Traverse relationships matching specified types and direction
3. Apply confidence filters
4. Return subgraph with nodes, relationships, and evidence quotes

## Output

Subgraph containing:
- Connected nodes with metadata
- Relationship types and confidence scores
- Evidence quotes from source documents

## Example Use

"Find all Value Drivers reachable from Capability X"
