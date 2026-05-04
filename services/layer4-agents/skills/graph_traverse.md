---
name: graph_traverse
description: Traverses the knowledge graph to find connected entities and relationship paths
---

# Graph Traverse

Performs multi-hop graph traversal to discover entity relationships and paths.

## Parameters

- `start_entity_id`: UUID of the starting entity node
- `relationship_types`: List of relationship predicates to follow
- `max_depth`: Maximum traversal depth (hops)
- `filters`: Optional entity type filters and property constraints

## Output

Returns traversal results with paths, connected entities, relationship metadata, and cycle detection flags.
