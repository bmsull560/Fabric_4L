---
name: semantic_search
description: Performs semantic search across entities using vector similarity and text matching
---

# Semantic Search

Combines vector similarity search with BM25 text ranking for hybrid entity retrieval.

## Parameters

- `query`: Natural language search query
- `entity_types`: Optional filter by entity types
- `top_k`: Number of results to return
- `min_confidence`: Minimum relevance threshold

## Output

Returns ranked search results with entity metadata, similarity scores, and source attribution.
