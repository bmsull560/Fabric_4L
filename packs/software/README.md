# Software Value Pack

Complete value model for B2B SaaS and enterprise software - customer economics, platform efficiency, and revenue optimization.

## Overview

This Value Pack provides pre-built value models, formulas, and workflows for SaaS business case development. It includes comprehensive definitions for customer acquisition economics, retention/upsell value drivers, and operational efficiency metrics.

## Pack Contents

| File | Description |
|------|-------------|
| `ontology.json` | 13 entities (4 capabilities, 3 use cases, 3 personas, 3 value drivers) with 9 relationships |
| `formulas.json` | 7 SaaS formulas with governance metadata |
| `variables.json` | 30 variable definitions with CRM/ERP/Cloud source bindings |
| `workflow_template.json` | 5-phase business case workflow with 20 tasks |

## Quick Start

### Load the Pack

```python
import json

# Load ontology
with open('packs/software/ontology.json') as f:
    ontology = json.load(f)

# Load formulas
with open('packs/software/formulas.json') as f:
    formulas = json.load(f)

# Load variables
with open('packs/software/variables.json') as f:
    variables = json.load(f)
```

### Use a Formula

```python
# Example: Calculate CAC Efficiency ROI
variables = {
    "Current_CAC": 25000,
    "Target_CAC": 20000,
    "New_Customers_Per_Year": 500,
    "Program_Investment": 500000
}

# Formula: ((Current_CAC - Target_CAC) * New_Customers_Per_Year - Program_Investment) / Program_Investment * 100
roi = ((25000 - 20000) * 500 - 500000) / 500000 * 100
print(f"CAC Efficiency ROI: {roi:.1f}%")

# Example: Calculate NRR Improvement Value
nrr_vars = {
    "Beginning_ARR": 10000000,
    "Current_NRR": 105,
    "Target_NRR": 115,
    "Implementation_Cost": 750000
}

# Formula: Beginning_ARR * (Target_NRR - Current_NRR) / 100 - Implementation_Cost
nrr_value = 10000000 * (115 - 105) / 100 - 750000
print(f"NRR Improvement Value: ${nrr_value:,.0f}")
```

## Included Formulas

| ID | Name | Type | Status | Business Driver |
|----|------|------|--------|-----------------|
| sw-f-001 | Customer Acquisition Efficiency ROI | ROI | Active | Capital Efficiency |
| sw-f-002 | Net Revenue Retention Improvement Value | Custom | Active | Revenue Enhancement |
| sw-f-003 | Churn Reduction Value | Custom | Active | Revenue Protection |
| sw-f-004 | Gross Margin Expansion Value | Custom | Active | Cost Reduction |
| sw-f-005 | Platform Engineering ROI | ROI | Active | Capital Efficiency |
| sw-f-006 | AI Feature Monetization Value | Custom | Draft | Revenue Enhancement |
| sw-f-007 | Support Efficiency Improvement | Custom | Active | Cost Reduction |

## Key Variables

### Revenue Metrics
- `ARR` - Annual Recurring Revenue
- `ACV` - Average Contract Value
- `Beginning_ARR` - ARR at period start
- `Current_NRR` - Net Revenue Retention percentage
- `Target_NRR` - Target NRR after improvements

### Acquisition Metrics
- `Current_CAC` - Customer Acquisition Cost
- `Target_CAC` - Target CAC after efficiency programs
- `New_Customers_Per_Year` - Annual new logo acquisition

### Retention Metrics
- `Current_Churn_Rate` - Annual logo churn percentage
- `Target_Churn_Rate` - Target churn after retention programs
- `Total_Customers` - Active customer count
- `Avg_Customer_Lifespan_Years` - Average customer tenure

### Operational Metrics
- `Current_Gross_Margin` - Gross margin percentage
- `Target_Gross_Margin` - Target gross margin
- `Infrastructure_Investment` - Annual infrastructure spend
- `Platform_Investment` - Developer platform investment
- `Developer_Hours_Saved_Per_Year` - Productivity gains from platform

### Support Metrics
- `Current_Tickets_Per_Customer` - Support volume per customer
- `Target_Tickets_Per_Customer` - Target ticket volume
- `Cost_Per_Support_Ticket` - Fully loaded ticket resolution cost

## Testing

Run the pack test suite:

```bash
# From repository root
pytest packs/software/tests/ -v

# Or with specific test categories
pytest packs/software/tests/test_pack_integrity.py -v
pytest packs/software/tests/test_formula_execution.py -v
pytest packs/software/tests/test_ontology_relationships.py -v
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
- AI/ML Platform - ML infrastructure for predictive features
- Developer Platform - Self-service infrastructure and CI/CD
- Customer Success Automation - Health monitoring and proactive interventions
- Usage-Based Billing - Metered billing infrastructure

**Use Cases:**
- Predictive Churn Prevention - Identify at-risk customers proactively
- Developer Self-Service - Eliminate platform team bottlenecks
- Expansion Revenue Capture - Automated upsell identification

**Personas:**
- Chief Revenue Officer - Revenue growth and retention strategy
- VP of Engineering - Delivery velocity and team productivity
- VP of Customer Success - Retention, expansion, customer outcomes

**Value Drivers:**
- Net Revenue Retention - Annual revenue from existing customers
- Customer Acquisition Efficiency - CAC and payback period
- Gross Margin - Revenue less COGS

## Workflow Phases

1. **Discovery & Data Collection** (5 days) - CRM/financial metrics, infrastructure costs, developer productivity, support operations
2. **Value Analysis & Opportunity Sizing** (7 days) - CAC efficiency, NRR improvement, churn reduction, margin expansion, platform ROI, AI monetization
3. **Validation & Benchmarking** (5 days) - SaaS benchmark comparison, technical feasibility, financial model validation
4. **Recommendations & Business Case** (6 days) - Prioritized roadmap, investment requirements, documentation
5. **Review & Approval** (3 days) - Internal review, stakeholder review, final approval

## Industry Benchmarks

| Metric | Best-in-Class | Good | Average | Poor |
|--------|---------------|------|---------|------|
| NRR | 125%+ | 110%+ | 100%+ | <90% |
| CAC | $15K | $25K | $40K | $60K+ |
| Churn (Annual) | 5% | 8% | 12% | 20%+ |
| Gross Margin | 85%+ | 78% | 70% | <60% |
| Support Tickets/Customer | 2 | 4 | 6 | 10+ |

## Pack Metadata

- **Pack ID:** software-v1
- **Version:** 1.0.0
- **Industry:** Software / B2B SaaS
- **Created:** 2026-04-11

## See Also

- [Pack Authoring Guide](../../docs/pack_authoring_guide.md) - How to create new Value Packs
- [Manufacturing Value Pack](../manufacturing/README.md) - Reference implementation
- [Product Brief](../../docs/product_brief.md) - Value Fabric platform overview

## License

Internal use only - SaaS Value Engineering Team
