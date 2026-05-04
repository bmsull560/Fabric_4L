# ValuePack Evidence Framework Extraction Prompt

Extract proof requirements and evidence hierarchy from industry documents for ValuePack Framework v1.0.

## Input
Industry compliance documents, audit requirements, case studies with evidence sections, or regulatory guidance.

## Output Format

```json
{
  "proof_requirements": [
    {
      "id": "snake_case_requirement_id",
      "requirement": "What proof is required",
      "evidence_type": "Type of evidence (e.g., audit, measurement, certification)",
      "minimum_level": 1|2|3|4|5
    }
  ],
  "evidence_framework": {
    "hierarchy": [
      {
        "level": 1,
        "label": "Peer-Reviewed / Audited",
        "requirements": ["Requirement 1", "Requirement 2"],
        "acceptable_sources": ["Source 1", "Source 2"]
      },
      {
        "level": 2,
        "label": "Third-Party Validated",
        "requirements": ["Requirement 1", "Requirement 2"],
        "acceptable_sources": ["Source 1", "Source 2"]
      },
      {
        "level": 3,
        "label": "Customer Measured",
        "requirements": ["Requirement 1", "Requirement 2"],
        "acceptable_sources": ["Source 1", "Source 2"]
      },
      {
        "level": 4,
        "label": "Platform Benchmarked",
        "requirements": ["Requirement 1", "Requirement 2"],
        "acceptable_sources": ["Source 1", "Source 2"]
      },
      {
        "level": 5,
        "label": "Industry Estimated",
        "requirements": ["Requirement 1", "Requirement 2"],
        "acceptable_sources": ["Source 1", "Source 2"]
      }
    ],
    "required_level": 3,
    "validation_rules": ["Custom rule 1", "Custom rule 2"]
  },
  "metadata": {
    "deal_size_range": "Typical contract value",
    "sales_cycle_length": "Average time to close",
    "switching_cost": "low|medium|high",
    "data_richness": "low|medium|high",
    "feedback_loop_speed": "slow|medium|fast"
  }
}
```

## Evidence Hierarchy Levels

### Level 1: Peer-Reviewed / Audited
- Academic or industry journal publication
- Big 4 audit firm validation
- Certified public accountant review

### Level 2: Third-Party Validated
- Industry analyst validation (Gartner, Forrester)
- Customer public testimonial with metrics
- Independent consultant assessment

### Level 3: Customer Measured
- Customer's own internal measurement
- Before/after comparison with methodology
- Time-bound tracking with baselines

### Level 4: Platform Benchmarked
- Aggregate platform data (anonymized)
- Cross-customer statistical analysis
- Platform-specific benchmarks

### Level 5: Industry Estimated
- Industry standard assumptions
- Comparable company analysis
- Market research estimates

## Proof Requirements Guidelines
- Max 3 requirements per industry
- Each must map to evidence hierarchy level
- Must be specific enough to verify
- Must align with industry regulations/compliance

## Metadata Guidelines
- **deal_size_range**: ACV or TCV ranges (e.g., "$50K-500K")
- **sales_cycle_length**: Time from first meeting to close
- **switching_cost**: Technical, data, and process switching difficulty
- **data_richness**: Availability of metrics for modeling
- **feedback_loop_speed**: How quickly value becomes measurable

## Confidence Scoring
Include: `"evidence_extraction_confidence": 0.82`
