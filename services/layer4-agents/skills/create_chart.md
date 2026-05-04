---
name: create_chart
description: Creates charts and visualizations for business cases
---

# Create Chart

Create charts and visualizations for business case presentations.

## Parameters

- `chart_type`: enum — bar, line, pie, table, funnel (required)
- `data`: array — Chart data points (required)
- `title`: string — Chart title (required)
- `config`: object — Additional chart configuration (optional)

## Steps

1. Validate data structure for chart type
2. Transform data to chart format
3. Apply configuration options
4. Return chart data structure

## Output

Returns CreateChartOutput with:
- `chart_data`: Structured chart data
- `image_data`: Optional rendered image bytes
- `image_url`: Optional hosted image URL
