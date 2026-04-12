# Life Sciences Value Pack

Complete value model for pharmaceutical and biotech industries - clinical development, regulatory efficiency, and R&D optimization.

## Overview

This Value Pack provides pre-built value models, formulas, and workflows for Life Sciences business case development. It includes comprehensive definitions for clinical trial acceleration, regulatory submission optimization, manufacturing yield improvement, and R&D portfolio efficiency.

## Pack Contents

| File | Description |
|------|-------------|
| `ontology.json` | 13 entities (4 capabilities, 3 use cases, 3 personas, 3 value drivers) with 9 relationships |
| `formulas.json` | 7 pharma/biotech formulas with governance metadata |
| `variables.json` | 33 variable definitions with CTMS/MES/QMS source bindings |
| `workflow_template.json` | 5-phase business case workflow with 25 tasks |

## Quick Start

### Load the Pack

```python
import json

# Load ontology
with open('packs/life-sciences/ontology.json') as f:
    ontology = json.load(f)

# Load formulas
with open('packs/life-sciences/formulas.json') as f:
    formulas = json.load(f)

# Load variables
with open('packs/life-sciences/variables.json') as f:
    variables = json.load(f)
```

### Use a Formula

```python
# Example: Calculate Clinical Trial Acceleration Value
variables = {
    "Current_Timeline_Months": 72,
    "Target_Timeline_Months": 60,
    "Peak_Annual_Revenue": 500_000_000,
    "NPV_Discount_Factor": 0.85,
    "Acceleration_Program_Cost": 10_000_000
}

# Formula: (72 - 60) / 12 * 500M * 0.85 - 10M
months_saved = variables["Current_Timeline_Months"] - variables["Target_Timeline_Months"]
years_saved = months_saved / 12
revenue_accelerated = years_saved * variables["Peak_Annual_Revenue"]
npv_value = revenue_accelerated * variables["NPV_Discount_Factor"]
net_value = npv_value - variables["Acceleration_Program_Cost"]

print(f"Trial Acceleration Value: ${net_value:,.0f}")

# Example: Calculate Manufacturing Yield Improvement
yield_vars = {
    "Current_Yield_Percent": 75,
    "Target_Yield_Percent": 85,
    "Annual_Batch_Count": 100,
    "Batch_Product_Value": 5_000_000,
    "Process_Optimization_Investment": 5_000_000
}

# Formula: 100 * (85 - 75) / 100 * 5M - 5M
additional_batches = yield_vars["Annual_Batch_Count"] * (yield_vars["Target_Yield_Percent"] - yield_vars["Current_Yield_Percent"]) / 100
yield_value = additional_batches * yield_vars["Batch_Product_Value"] - yield_vars["Process_Optimization_Investment"]

print(f"Yield Improvement Value: ${yield_value:,.0f}")
```

## Included Formulas

| ID | Name | Type | Status | Business Driver |
|----|------|------|--------|-----------------|
| ls-f-001 | Clinical Trial Acceleration Value | NPV | Active | Capital Efficiency |
| ls-f-002 | Patient Recruitment Efficiency | Custom | Active | Cost Reduction |
| ls-f-003 | R&D Portfolio ROI | ROI | Active | Capital Efficiency |
| ls-f-004 | Regulatory Submission Efficiency | Custom | Active | Capital Efficiency |
| ls-f-005 | Biomanufacturing Yield Improvement | Custom | Active | Cost Reduction |
| ls-f-006 | Quality Event Risk Reduction | Custom | Active | Risk Mitigation |
| ls-f-007 | Real-World Evidence Value | Custom | Draft | Revenue Enhancement |

## Key Variables

### Clinical Development Metrics
- `Current_Timeline_Months` - Months from IND to approval (baseline)
- `Target_Timeline_Months` - Months with acceleration initiatives
- `Current_Cost_Per_Patient` - Fully-loaded recruitment cost
- `Target_Cost_Per_Patient` - Optimized recruitment cost
- `Required_Patients` - Total enrollment needed
- `Baseline_Success_Rate` - Current probability of success
- `Improved_Success_Rate` - Target probability with analytics

### Regulatory Metrics
- `Baseline_Review_Months` - Typical regulatory review time
- `Target_Review_Months` - Optimized review time
- `eCTD_Investment` - Regulatory systems investment
- `FTE_Efficiency_Savings` - Regulatory FTE savings

### Manufacturing Metrics
- `Current_Yield_Percent` - Current batch success rate
- `Target_Yield_Percent` - Target yield with optimization
- `Annual_Batch_Count` - Total batches per year
- `Batch_Product_Value` - Revenue per successful batch
- `Current_Deviation_Rate` - Deviation rate (baseline)
- `Target_Deviation_Rate` - Target deviation rate
- `Potential_Recall_Cost` - Estimated recall cost

### Financial Metrics
- `Peak_Annual_Revenue` - Peak revenue forecast
- `Pipeline_Risk_Adjusted_NPV` - Pipeline NPV
- `NPV_Discount_Factor` - Time-value discount factor
- `Label_Expansion_NPV` - Label expansion opportunity NPV

## Testing

Run the pack test suite:

```bash
# From repository root
pytest packs/life-sciences/tests/ -v

# Or with specific test categories
pytest packs/life-sciences/tests/test_pack_integrity.py -v
pytest packs/life-sciences/tests/test_formula_execution.py -v
pytest packs/life-sciences/tests/test_ontology_relationships.py -v
```

## Ontology Structure

```
┌─────────────────┐     ENABLES      ┌───────────────┐
│   Capability    │ ─────────────────>│   UseCase     │
│  (Platform)     │                   │  (Scenario)   │
└─────────────────┘                   └───────────────┘
                                              │
                                              │ BENEFITS
                                              ▼
┌─────────────────┐     DRIVES       ┌───────────────┐
│  ValueDriver    │ <────────────────│    Persona    │
│    (KPIs)       │                  │  (Executive)  │
└─────────────────┘                  └───────────────┘
```

**Capabilities:**
- Clinical Data Analytics - AI-powered trial monitoring and safety detection
- Patient Engagement Platform - DCT and digital recruitment infrastructure
- Regulatory Intelligence - Submission strategy and precedent analysis
- Quality Management System - Automated deviation and CAPA management

**Use Cases:**
- Decentralized Clinical Trials - Remote patient participation
- Adaptive Trial Design - Interim analysis and protocol optimization
- Continuous Process Verification - Real-time manufacturing monitoring

**Personas:**
- Chief Medical Officer - Clinical development strategy and success rates
- Head of Clinical Operations - Trial execution and enrollment velocity
- VP Regulatory Affairs - Submission strategy and approval timelines

**Value Drivers:**
- Time-to-Market - Total development timeline
- Clinical Trial Success Rate - Probability of regulatory approval
- Manufacturing Yield - Batch success rate

## Workflow Phases

1. **Discovery & Data Collection** (7 days) - Clinical timelines, regulatory metrics, manufacturing quality, portfolio positioning
2. **Value Analysis & Opportunity Sizing** (10 days) - Trial acceleration, recruitment efficiency, R&D ROI, regulatory efficiency, yield improvement, quality risk, RWE value
3. **Validation & Benchmarking** (7 days) - Industry benchmarks, clinical feasibility, technical feasibility, risk-adjusted model
4. **Recommendations & Business Case** (8 days) - Prioritized roadmap, investment requirements, executive business case
5. **Review & Approval** (4 days) - Cross-functional review, leadership review, final investment decision

## Industry Benchmarks

| Metric | Best-in-Class | Average | Poor |
|--------|---------------|---------|------|
| Time to Market | 48 months | 72 months | 108 months |
| P(Success) Phase 1 | 30% | 15% | 8% |
| Patient Recruitment | $20K/patient | $35K/patient | $50K/patient |
| Manufacturing Yield | 95% | 80% | 65% |
| Deviation Rate | 3% | 8% | 15% |

## Pack Metadata

- **Pack ID:** life-sciences-v1
- **Version:** 1.0.0
- **Industry:** Life Sciences / Pharma / Biotech
- **Created:** 2026-04-11

## See Also

- [Pack Authoring Guide](../../docs/pack_authoring_guide.md) - How to create new Value Packs
- [Manufacturing Value Pack](../manufacturing/README.md) - Reference implementation
- [Software Value Pack](../software/README.md) - B2B SaaS value pack
- [Product Brief](../../docs/product_brief.md) - Value Fabric platform overview

## License

Internal use only - Life Sciences Value Engineering Team
