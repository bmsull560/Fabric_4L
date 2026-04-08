---
description: Show complete lineage of any generated output
---

# Provenance Tracer Workflow

Use this workflow to trace the complete lineage of any generated output.

## Parameters

- `output_id`: ID of generated document or calculation (string, required)
- `depth`: FULL | SUMMARY - Level of detail (default: FULL)

## Steps

1. Retrieve the output by ID
2. Trace back through generation steps
3. Identify LLM calls made
4. Link to source extractions
5. Map to original source documents
6. Present chain of custody

## Output

Provenance chain:
- Chain of custody from source to output
- LLM calls made during generation
- Source documents with timestamps
- Confidence scores at each step
- Extraction evidence and quotes

## Example Use

"Where did this $2.5M ROI number come from?"
