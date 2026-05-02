---
name: find_paths
description: Finds connection paths between two entities in the graph
---

# Find Paths

Find paths between two entities in the knowledge graph using shortest path algorithms.

## Parameters

- `source_id`: string — Starting entity ID (required)
- `target_id`: string — Target entity ID (required)
- `max_length`: integer — Maximum path length 1-10 (default: 6)
- `relationship_types`: array — Allowed relationship types (optional)

## Steps

1. Validate source and target entities exist
2. Execute shortest path query using allShortestPaths
3. Return all paths within max_length constraint

## Output

Returns FindPathsOutput with:
- `paths`: array of path objects with nodes and relationships
- `shortest_path_length`: length of shortest path found
