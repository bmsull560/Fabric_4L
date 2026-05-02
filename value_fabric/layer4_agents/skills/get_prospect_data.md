---
name: get_prospect_data
description: Retrieves prospect profile, interactions, and opportunities from CRM
---

# Get Prospect Data

Retrieve comprehensive prospect data from CRM systems (Salesforce or HubSpot).

## Parameters

- `prospect_id`: string — CRM prospect/company ID (required)
- `data_types`: array — Data to fetch: profile, interactions, opportunities (default: all)

## Steps

1. Authenticate with CRM API
2. Fetch requested data types
3. Normalize data format
4. Return structured prospect data

## Output

Returns GetProspectDataOutput with:
- `profile`: Company profile data
- `interactions`: List of interactions/activities
- `opportunities`: List of opportunities/deals
- `custom_fields`: Custom CRM fields
