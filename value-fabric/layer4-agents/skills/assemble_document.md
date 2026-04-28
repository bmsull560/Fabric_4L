---
name: assemble_document
description: Assembles business case sections into PDF, DOCX, or HTML
---

# Assemble Document

Assemble business case sections into complete documents in PDF, DOCX, or HTML format.

## Parameters

- `sections`: array — Document sections with title and content (required)
- `template`: string — Template name (default: business_case)
- `output_format`: enum — pdf, docx, html (default: pdf)
- `branding`: object — Branding config: company_name, logo_url, etc. (optional)

## Steps

1. Validate section structure
2. Apply template and branding
3. Generate document in specified format
4. Calculate page count and file size
5. Return document bytes

## Output

Returns AssembleDocumentOutput with:
- `document_bytes`: Document as bytes
- `document_url`: Optional hosted URL
- `page_count`: Estimated page count
- `file_size_bytes`: Document size
