---
name: format_table
description: Formats data as HTML, Markdown, or CSV tables
---

# Format Table

Format data as HTML, Markdown, or CSV tables for various output formats.

## Parameters

- `headers`: array — Column headers (required)
- `rows`: array — Data rows as arrays (required)
- `format`: enum — html, markdown, csv (default: html)
- `sort_column`: integer — Column index to sort by (optional)

## Steps

1. Apply sorting if specified
2. Format according to output format
3. Generate formatted table string
4. Return with metadata

## Output

Returns FormatTableOutput with:
- `formatted`: Formatted table string
- `row_count`: Number of rows
