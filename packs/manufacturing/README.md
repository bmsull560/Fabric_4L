# Manufacturing Value Pack

Complete reference implementation of a Value Pack for the manufacturing industry.

## Overview

This Value Pack provides pre-built value models, formulas, and workflows for manufacturing operations excellence initiatives. It includes comprehensive definitions for OEE, quality, maintenance, and energy efficiency value drivers.

## Pack Contents

| File | Description |
|------|-------------|
| `ontology.json` | 10 entities (3 capabilities, 2 use cases, 2 personas, 3 value drivers) with 6 relationships |
| `formulas.json` | 7 manufacturing formulas with governance metadata |
| `variables.json` | 35 variable definitions with MES/ERP/CMMS source bindings |
| `workflow_template.json` | 5-phase business case workflow with 21 tasks |

## Quick Start

### Load the Pack

```python
import json

# Load ontology
with open('packs/manufacturing/ontology.json') as f:
    ontology = json.load(f)

# Load formulas
with open('packs/manufacturing/formulas.json') as f:
    formulas = json.load(f)

# Load variables
with open('packs/manufacturing/variables.json') as f:
    variables = json.load(f)
```

### Use a Formula

```python
# Example: Calculate OEE Improvement ROI
variables = {
    "Current_OEE": 75.0,
    "Baseline_OEE": 60.0,
    "Annual_Production_Value": 10000000,
    "Margin_Percentage": 25.0,
    "Annual_Implementation_Cost": 500000
}

# Formula: (((Current_OEE - Baseline_OEE) / 100) * Annual_Production_Value * Margin_Percentage) - Annual_Implementation_Cost
roi = (((75 - 60) / 100) * 10000000 * 0.25) - 500000
print(f"OEE Improvement ROI: ${roi:,.0f}")
```

## Included Formulas

| ID | Name | Type | Status |
|----|------|------|--------|
| mfg-f-001 | OEE Improvement ROI | ROI | Active |
| mfg-f-002 | Unplanned Downtime Cost | Custom | Active |
| mfg-f-003 | Quality Defect Cost | Custom | Active |
| mfg-f-004 | Energy Cost Savings | Custom | Draft |
| mfg-f-005 | Predictive Maintenance ROI | ROI | Active |
| mfg-f-006 | Throughput Improvement Value | Custom | Active |
| mfg-f-007 | First Pass Yield Improvement Value | Custom | Draft |

## Key Variables

### OEE Metrics
- `Current_OEE` - Overall Equipment Effectiveness percentage
- `Availability` - Equipment availability rate
- `Performance` - Equipment performance ratio
- `Quality_Rate` - First pass quality rate

### Maintenance KPIs
- `Average_Downtime_Hours_Per_Month` - Monthly unplanned downtime
- `Annual_Emergency_Repairs` - Emergency repair frequency
- `Avoided_Downtime_Value` - Value of prevented downtime

### Quality Metrics
- `Defect_Rate` - Manufacturing defect percentage
- `First_Pass_Yield` - FPY percentage
- `Scrap_Cost_Per_Unit` - Cost of scrapped units

## Testing

Run the pack test suite:

```bash
# From repository root
pytest packs/manufacturing/tests/ -v

# Or with specific test categories
pytest packs/manufacturing/tests/test_pack_integrity.py -v
pytest packs/manufacturing/tests/test_formula_execution.py -v
pytest packs/manufacturing/tests/test_ontology_relationships.py -v
```

## Ontology Structure

```
┌─────────────────┐     ENABLES      ┌───────────────┐
│   Capability    │ ─────────────────>│   UseCase     │
│  (Technology)   │                   │  (Scenario)   │
└─────────────────┘                   └───────────────┘
                                              │
                                              │ BENEFITS
                                              ▼
┌─────────────────┐     DRIVES       ┌───────────────┐
│  ValueDriver    │ <────────────────│    Persona    │
│    (KPIs)       │                  │  (Stakeholder)│
└─────────────────┘                  └───────────────┘
```

## Workflow Phases

1. **Discovery & Data Collection** (3 days) - Baseline OEE, quality metrics, maintenance costs, energy consumption
2. **Value Analysis & Opportunity Sizing** (5 days) - ROI calculations for improvement initiatives
3. **Validation & Benchmarking** (3 days) - Industry benchmark comparison, technical feasibility review
4. **Recommendations & Business Case** (4 days) - Prioritized roadmap, investment requirements, documentation
5. **Review & Approval** (2 days) - Internal review, stakeholder review, final approval

## Industry Benchmarks

| Metric | World Class | Average | Below Average |
|--------|-------------|---------|---------------|
| OEE | 85% | 60% | 40% |
| First Pass Yield | 99% | 95% | 85% |
| Downtime | 10 hrs/mo | 40 hrs/mo | 100 hrs/mo |

## Pack Metadata

- **Pack ID:** manufacturing-v1
- **Version:** 1.0.0
- **Industry:** Manufacturing
- **Created:** 2024-04-10

## See Also

- [Pack Authoring Guide](../../docs/pack_authoring_guide.md) - How to create new Value Packs
- [Product Brief](../../docs/product_brief.md) - Value Fabric platform overview

## License

Internal use only - Manufacturing Value Engineering Team
