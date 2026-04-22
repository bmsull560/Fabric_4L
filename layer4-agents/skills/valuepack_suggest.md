---
name: valuepack_suggest
description: Suggest the most relevant ValuePack(s) based on prospect profile and business context
tags: [valuepack, recommendation, prospecting]
inputs:
  - name: prospect_profile
    type: object
    description: Prospect company profile
    required: true
    properties:
      industry: "Primary industry"
      sub_industry: "Sub-industry/sector"
      employee_count: "Number of employees"
      annual_revenue: "Annual revenue"
      pain_points: "List of business challenges"
      current_tech_stack: "Current technology stack"
  - name: criteria
    type: object
    description: Selection criteria weights
    required: false
outputs:
  - name: suggestions
    type: array
    description: Ranked ValuePack suggestions with match scores
---

# ValuePack Suggest Skill

## Purpose
Intelligently match prospect profiles to the most relevant ValuePacks based on:
- Industry alignment (exact match → related → adjacent)
- Pain point mapping to value drivers
- Company size and deal size range compatibility
- Technology stack fit
- Tier appropriateness (traction vs complexity)

## Usage

```yaml
skill: valuepack_suggest
inputs:
  prospect_profile:
    industry: "Healthcare"
    sub_industry: "Medical Devices"
    employee_count: 5000
    annual_revenue: "$500M"
    pain_points: ["Long sales cycles", "Complex approval processes", "Cost pressure from CMS"]
    current_tech_stack: ["Salesforce", "SAP", "Epic EHR"]
  criteria:
    prioritize_tier: 1
    min_match_score: 0.7
```

## Matching Algorithm

1. **Industry Match (40% weight)**
   - Exact industry match: 1.0
   - Related industry (shared ontology tag): 0.7
   - Adjacent industry (same tier/characteristics): 0.5

2. **Pain Point Alignment (30% weight)**
   - Each prospect pain point matched to ValuePack driver: +0.1
   - Use case directly addresses pain: +0.15

3. **Size Compatibility (20% weight)**
   - Employee count within typical range: 1.0
   - Revenue within deal size range: 1.0
   - Outside range but within 2x: 0.5

4. **Tech Stack Fit (10% weight)**
   - Platform integrations available: 1.0
   - API compatibility: 1.0
   - Requires custom integration: 0.5

## Output Schema

```json
{
  "suggestions": [
    {
      "industry_id": "healthcare",
      "display_name": "Healthcare & MedTech",
      "match_score": 0.92,
      "match_breakdown": {
        "industry_match": 1.0,
        "pain_point_alignment": 0.9,
        "size_compatibility": 0.85,
        "tech_fit": 1.0
      },
      "recommended_drivers": [
        {
          "driver_id": "cost_avoidance",
          "relevance": "Addresses CMS cost pressure pain point"
        }
      ],
      "suggested_use_cases": [
        {
          "use_case_id": "readmission_reduction",
          "relevance": "Matches cost pressure context"
        }
      ]
    }
  ],
  "recommendation_summary": "Healthcare ValuePack is ideal match with 92% score"
}
```

## Implementation

1. Query Layer 3 for all ValuePacks
2. Apply matching algorithm to each
3. Filter by minimum match score
4. Rank and return top 3

## API Call
```
GET /v1/valuepacks
Then local scoring algorithm
```
