---
name: update_opportunity
description: Updates opportunity fields and optionally notifies owner
---

# Update Opportunity

Update opportunity fields in CRM systems (Salesforce or HubSpot).

## Parameters

- `opportunity_id`: string — Opportunity ID to update (required)
- `updates`: object — Field updates as key-value pairs (required)
- `notify_owner`: boolean — Send notification to owner (default: true)

## Steps

1. Validate field updates
2. Authenticate with CRM API
3. Apply updates via PATCH request
4. Optionally trigger owner notification
5. Return success status

## Output

Returns UpdateOpportunityOutput with:
- `success`: Boolean indicating update success
- `opportunity_id`: ID of updated opportunity
- `updated_fields`: List of changed fields
- `error`: Error message if failed
