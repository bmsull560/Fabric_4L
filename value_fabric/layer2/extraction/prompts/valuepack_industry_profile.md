# ValuePack Industry Profile Extraction Prompt

Extract structured industry profile information suitable for ValuePack Framework v1.0 from the provided document.

## Input
Industry document, whitepaper, market analysis, or research report.

## Output Format
Produce JSON matching the industry profile structure:

```json
{
  "display_name": "Industry Name (Sector/Sub-sector)",
  "description": "2-3 sentence overview of industry and value creation patterns",
  "tier": 1|2|3,
  "primary_value_drivers": [
    {
      "id": "snake_case_identifier",
      "name": "Human-readable driver name",
      "description": "What this driver means in this industry",
      "typical_impact": "Quantified range (e.g., $200K-1M or 10-25%)",
      "measurement_approach": "How organizations measure this"
    }
  ],
  "core_use_cases": [
    {
      "id": "snake_case_identifier",
      "name": "Use case name",
      "description": "What customers actually buy",
      "target_persona": "Primary buyer/user",
      "business_problem": "Problem this solves"
    }
  ],
  "why_it_wins": [
    {
      "statement": "Platform-specific win statement",
      "differentiation": "How this differs from generic claims",
      "proof_point": "Specific supporting evidence"
    }
  ]
}
```

## Extraction Guidelines

### Value Drivers (max 4)
- Identify what MOVES MONEY in this industry
- Look for: cost reduction, revenue growth, risk mitigation, efficiency gains
- Each driver must be measurable and industry-specific
- Avoid generic drivers that apply to all industries

### Use Cases (max 4)
- Identify what customers ACTUALLY BUY
- Map to specific product capabilities
- Include target persona and their pain point
- Must connect to at least one value driver

### Tier Classification
- **Tier 1 (Immediate Traction)**: Clear metrics, short sales cycle, high data availability
- **Tier 2 (High ROI, Underserved)**: Strong value but less competition, may need education
- **Tier 3 (Complex but Powerful)**: Long sales cycle, complex value chains, high rewards

### Win Statements (max 3)
- Must be SPECIFIC to the platform (not generic vendor claims)
- Must have PROOF POINTS from the document
- Must be DIFFERENTIATED from competitors

## Examples

**Good Value Driver:**
```json
{
  "id": "downtime_reduction",
  "name": "Production Downtime Reduction",
  "description": "Minutes of unplanned production line downtime avoided through predictive maintenance",
  "typical_impact": "$50K-200K per hour saved",
  "measurement_approach": "MTTR and MTBF tracking with cost attribution"
}
```

**Bad Value Driver:**
```json
{
  "id": "cost_savings",
  "name": "Cost Savings",
  "description": "Saves money",
  "typical_impact": "Significant",
  "measurement_approach": "Various methods"
}
```

## Confidence Scoring
Rate extraction confidence for each field:
- **HIGH**: Explicitly stated with supporting data
- **MEDIUM**: Inferred from context with reasonable certainty
- **LOW**: Ambiguous or missing information

Include confidence score in output: `"extraction_confidence": 0.85`
