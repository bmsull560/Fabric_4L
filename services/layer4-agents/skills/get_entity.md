---
name: get_entity
description: Retrieves a specific entity by ID with optional relationships
---

# Get Entity

Retrieve a specific entity by ID from the knowledge graph, with optional relationship data.

## Parameters

- `entity_id`: string — Unique identifier of the entity (required)
- `include_relationships`: boolean — Include connected relationships (default: true)
- `depth`: integer — Relationship depth to traverse 0-3 (default: 1)

## Steps

1. Query Neo4j for entity by ID
2. If include_relationships, fetch connected relationships up to depth
3. Return entity data with optional relationship graph

## Output

Returns GetEntityOutput with:
- `entity`: object with entity properties (null if not found)
- `relationships`: array of connected relationships
- `found`: boolean indicating if entity exists
