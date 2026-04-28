---
name: query_graph
description: Executes Cypher queries against the Neo4j knowledge graph
---

# Query Graph

Execute Cypher queries against the Neo4j knowledge graph to retrieve structured data about entities, relationships, and paths.

## Parameters

- `cypher_query`: string — Cypher query to execute (required)
- `parameters`: object — Query parameters for safe variable substitution (optional)
- `read_only`: boolean — Whether query is read-only (default: true)

## Steps

1. Validate query is read-only (no CREATE, DELETE, SET, MERGE operations)
2. Execute Cypher query against Neo4j database
3. Return results with metadata including columns and row count

## Output

Returns QueryGraphOutput with:
- `results`: array of record objects
- `columns`: array of column names
- `row_count`: number of rows returned
- `execution_time_ms`: query execution time
