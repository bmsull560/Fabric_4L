---
name: validate_input
description: Validates input data against defined schemas
---

# Validate Input

Validate input data against common schemas like prospect_id, email, formula.

## Parameters

- `data`: object — Data to validate (required)
- `schema_name`: string — Schema to validate against (required)
- `strict`: boolean — Strict validation mode (default: true)

## Steps

1. Load schema definition
2. Validate data against schema rules
3. Collect validation errors
4. Return normalized data if valid

## Output

Returns ValidateInputOutput with:
- `valid`: Boolean validation result
- `errors`: Array of error messages
- `normalized`: Normalized data object
