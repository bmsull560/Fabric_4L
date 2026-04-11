---
name: multi-hop-reason
description: Answer complex questions requiring multiple graph traversals
---

# Multi-Hop Reasoning Workflow

Use this workflow to answer complex questions that require traversing multiple hops in the Knowledge Graph.

## Parameters

- `question`: Natural language question (string, required)
- `max_hops`: Integer for maximum traversal depth (default: 3)
- `require_evidence`: Boolean - Include supporting quotes (default: true)

## Steps

1. Parse the question into sub-queries
2. Identify starting entities
3. Execute multi-hop graph traversals
4. Collect evidence at each hop
5. Synthesize answer with reasoning chain
6. Include source citations

## Output

Structured answer containing:
- Synthesized response to the question
- Reasoning chain with traversal steps
- Evidence quotes from source documents
- Source citations with confidence scores

## Example Use

"Which personas benefit most from our AI capabilities in manufacturing?"
