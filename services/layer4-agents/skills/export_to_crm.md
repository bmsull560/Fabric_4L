---
name: export_to_crm
description: Exports notes, documents, or activities to CRM systems
---

# Export to CRM

Export notes, documents, or activities to Salesforce or HubSpot CRM.

## Parameters

- `entity_type`: enum — note, document, activity (required)
- `entity_data`: object — Entity content and metadata (required)
- `prospect_id`: string — Associated prospect/company ID (required)

## Steps

1. Authenticate with CRM API
2. Build entity-specific payload
3. Create or update CRM record
4. Return record ID and URL

## Output

Returns ExportToCRMOutput with:
- `crm_record_id`: Created/updated record ID
- `success`: Boolean status
- `url`: CRM record URL
- `error`: Error message if failed
