---
name: fetch_interaction_history
description: Retrieves interaction history including emails, calls, meetings
---

# Fetch Interaction History

Retrieve interaction history for a prospect from CRM systems.

## Parameters

- `prospect_id`: string — Prospect/company ID (required)
- `interaction_types`: array — Filter by types (optional)
- `since_date`: string — Start date filter ISO format (optional)
- `limit`: integer — Maximum results 1-200 (default: 50)

## Steps

1. Build SOQL/GraphQL query with filters
2. Execute CRM API request
3. Normalize interaction records
4. Generate activity summary
5. Return interactions with metadata

## Output

Returns FetchInteractionHistoryOutput with:
- `interactions`: Array of interaction records
- `total_count`: Total number of interactions
- `summary`: Human-readable activity summary
