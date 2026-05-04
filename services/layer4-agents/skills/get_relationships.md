---
name: get_relationships
description: Retrieves relationships for an entity with optional filtering
---

# Get Relationships

Retrieve relationships for a specific entity from the knowledge graph with filtering options.

## Parameters

- `entity_id`: string — Source entity ID (required)
- `predicate`: string — Relationship type filter (optional)
- `direction`: enum — outgoing, incoming, or both (default: both)
- `limit`: integer — Maximum results 1-500 (default: 50)

## Steps

1. Build Cypher query with optional predicate filter
2. Execute query to fetch relationships
3. Apply direction and limit filters
4. Return relationship list with metadata

## Output

Returns GetRelationshipsOutput with:
- `relationships`: array of relationship objects
- `total_count`: total number of relationships
