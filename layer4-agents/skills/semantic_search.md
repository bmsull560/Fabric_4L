---
name: semantic-search
description: Find entities by meaning, not just keywords
---

# Semantic Search Workflow

Use this workflow to find entities in the Knowledge Graph by semantic meaning.

## Parameters

- `query`: Natural language description (string, required)
- `entity_types`: List of entity types to search (e.g., Capability, UseCase, Persona, ValueDriver)
- `top_k`: Integer for number of results (default: 5)
- `similarity_threshold`: Float 0.0-1.0 (default: 0.8)

## Steps

1. Parse the natural language query
2. Convert to embedding vector
3. Search against entity embeddings
4. Filter by entity types and similarity threshold
5. Return ranked list of entities with similarity scores

## Output

Search results:
- Ranked list of matching entities
- Similarity scores (0.0-1.0)
- Entity metadata (type, description)
- Matched context snippets
- Confidence indicators

## Example Use

"Find capabilities related to predictive analytics"
