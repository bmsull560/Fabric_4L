---
name: valuepack_compare
description: Compare multiple ValuePacks across dimensions to identify similarities, differences, and optimal choices
tags: [valuepack, analysis, comparison]
inputs:
  - name: industry_ids
    type: array
    description: List of industry IDs to compare (2-5 industries)
    required: true
  - name: dimensions
    type: array
    description: Specific dimensions to compare (optional, defaults to all)
    required: false
outputs:
  - name: comparison_result
    type: object
    description: Detailed comparison across all dimensions
---

# ValuePack Compare Skill

## Purpose
Compare multiple ValuePacks side-by-side to identify:
- Shared value drivers and templates
- Industry-specific differentiators
- Best-fit ValuePack for a given context
- Gap analysis between industries

## Usage

```yaml
skill: valuepack_compare
inputs:
  industry_ids: ["enterprise_saas", "healthcare", "manufacturing"]
  dimensions: ["value_drivers", "economic_models", "proof_requirements"]
```

## Output Schema

```json
{
  "valuepacks": [
    {
      "industry_id": "enterprise_saas",
      "display_name": "Enterprise SaaS",
      "tier": 1,
      "primary_value_drivers": [...],
      "core_use_cases": [...]
    }
  ],
  "comparison_matrix": {
    "value_drivers": {
      "enterprise_saas": ["Headcount Efficiency", "Revenue Uplift"],
      "healthcare": ["Cost Avoidance", "Throughput Optimization"],
      "manufacturing": ["Downtime Reduction", "Yield Improvement"]
    },
    "tiers": {
      "enterprise_saas": "IMMEDIATE_TRACTION",
      "healthcare": "IMMEDIATE_TRACTION",
      "manufacturing": "HIGH_ROI_UNDERSERVED"
    }
  },
  "shared_templates": ["headcount_displacement", "efficiency_uplift"],
  "differentiation_analysis": {
    "enterprise_saas": "Differentiated by: Native sales cycle fit, CFO-driven buying",
    "healthcare": "Differentiated by: Clinical validation, regulatory defensibility"
  }
}
```

## Implementation

Call Layer 3 API:
```
POST /v1/valuepacks/compare
Body: { industry_ids, dimensions }
```

## Best Practices
- Compare 2-5 industries for meaningful analysis
- Focus on dimensions relevant to decision context
- Use shared_templates to identify reusable models
- Consider tier classification for prioritization
