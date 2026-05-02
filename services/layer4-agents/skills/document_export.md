---
name: document_export
description: Exports documents to CRM and storage systems
---

# Document Export

Export business case documents to CRM systems and cloud storage.

## Parameters

- `document_type`: enum — business_case, audit_report, roi_analysis (default: business_case)
- `business_case_data`: object — Structured business case data (optional)
- `template`: string — Custom HTML template (optional)
- `branding`: object — Branding configuration (optional)

## Steps

1. Validate business case data structure
2. Apply template and branding
3. Generate PDF document
4. Export to configured CRM/storage
5. Return success status and URL

## Output

Returns ExportDocumentOutput with:
- `pdf_bytes`: Generated PDF bytes
- `content_type`: MIME type
- `filename`: Suggested filename
- `success`: Boolean status
- `error`: Error message if failed
