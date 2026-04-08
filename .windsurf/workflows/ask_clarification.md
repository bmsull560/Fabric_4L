---
description: Ask user for missing information
---

# Clarification Request Workflow

Use this workflow to request missing or ambiguous information from the user.

## Parameters

- `missing_info`: Description of what's needed (string, required)
- `context`: Current context or partial results (string, optional)
- `urgency`: LOW | MEDIUM | HIGH (default: MEDIUM)
- `options`: List of suggested options (optional)

## Steps

1. Identify the missing information gap
2. Formulate clear, specific question
3. Provide context to help user respond
4. Present options if applicable
5. Document the clarification request
6. Wait for user response

## Output

Structured clarification request:
- Specific question(s) to answer
- Context explaining why it's needed
- Suggested options or examples
- Impact of providing vs not providing

## Example Use

"What industry is the prospect in? This affects benchmark comparisons."
