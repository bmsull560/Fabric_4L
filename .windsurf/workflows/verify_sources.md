---
description: Check source health and freshness
---

# Source Verifier Workflow

Use this workflow to verify the health, accessibility, and freshness of source documents.

## Parameters

- `source_ids`: List of source IDs to verify (optional, default: all)
- `checks`: List of checks (ACCESSIBILITY, FRESHNESS, COMPLETENESS, DUPLICATES) (default: all)
- `freshness_threshold_days`: Flag sources older than this (default: 90)

## Steps

1. Retrieve source URLs from the system
2. Check accessibility (HTTP status, robots.txt compliance)
3. Verify content freshness against threshold
4. Check for completeness of extracted data
5. Identify duplicate or near-duplicate sources
6. Report source health status

## Output

Source health report:
- Accessibility status per source
- Content freshness scores
- Missing or incomplete extractions
- Duplicate source detection
- Recommendations for re-crawl

## Example Use

"Check if any sources are stale or inaccessible"
