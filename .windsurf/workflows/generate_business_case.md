---
description: Create consultant-grade business case document
---

# Business Case Generator Workflow

Use this workflow to generate professional business case documents.

## Parameters

- `opportunity_context`: Object with prospect, industry, challenges
- `capability_ids`: List of capability IDs to include
- `output_format`: MARKDOWN | DOCX | PDF | PPTX (default: MARKDOWN)
- `sections`: List of sections to include (EXECUTIVE_SUMMARY, ROI_ANALYSIS, RISK_MITIGATION, etc.)
- `tone`: EXECUTIVE | TECHNICAL | FINANCIAL (default: EXECUTIVE)

## Steps

1. Gather context about prospect and industry
2. Resolve value trees for specified capabilities
3. Calculate ROI metrics
4. Generate narrative based on audience
5. Create executive summary
6. Assemble final document

## Output

Business case document:
- Executive summary
- ROI analysis with calculations
- Risk mitigation strategies
- Implementation roadmap
- Supporting evidence and citations
- Formatted per output_format specification

## Example Use

"Generate a business case for Target Corp using our analytics capabilities"
