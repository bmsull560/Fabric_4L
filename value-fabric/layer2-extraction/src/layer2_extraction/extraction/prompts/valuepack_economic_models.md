# ValuePack Economic Models Extraction Prompt

Extract economic model patterns and calculation templates from industry documents for ValuePack Framework v1.0.

## Input
Industry financial reports, ROI case studies, economic analyses, or value calculation methodologies.

## Output Format

```json
{
  "economic_model_types": [
    {
      "id": "snake_case_model_id",
      "name": "Model Name",
      "formula_shape": "Input → Calculation → Output (describe in words)",
      "inputs": ["input_1", "input_2", "input_3"],
      "output_unit": "What the output represents with units",
      "typical_range": "Expected output range"
    }
  ],
  "composable_model_templates": [
    {
      "template_id": "unique_template_id",
      "template_name": "Human-readable name",
      "formula_pattern": "Mathematical pattern (e.g., (A × B × C) - D)",
      "inputs_required": ["input_a", "input_b", "input_c", "input_d"],
      "output_definition": "What this calculates",
      "example_calculation": "Concrete numeric example"
    }
  ]
}
```

## Extraction Guidelines

### Economic Model Types (max 4)
Each model must have:
1. **Clear formula shape** showing input→calculation→output flow
2. **Specific inputs** that can be measured/obtained
3. **Output unit** with clear business meaning (not just "$")
4. **Typical range** based on industry data

### Formula Shape Examples
- GOOD: `(Hours Saved × Hourly Rate × Headcount) - Tool Cost = Annual Savings`
- BAD: `Calculate savings based on efficiency gains`

### Composable Templates
Identify reusable patterns that could apply to multiple industries:
1. **Headcount displacement**: Labor efficiency models
2. **Asset utilization**: Equipment/throughput optimization
3. **Risk avoidance**: Loss prevention calculations
4. **Revenue velocity**: Speed-to-revenue models

### Template Requirements
- Must have clear mathematical pattern
- Must specify all required inputs
- Must include concrete numeric example
- Must show reusability potential (2+ industries)

## Confidence Scoring
- **HIGH**: Document includes actual formulas or calculation spreadsheets
- **MEDIUM**: Implied calculations from case studies
- **LOW**: Vague value claims without quantification

Include: `"model_extraction_confidence": 0.75`
