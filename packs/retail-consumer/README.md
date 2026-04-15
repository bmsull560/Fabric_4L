# Retail & Consumer Value Pack

Complete value model for retail, CPG, and consumer brands - omnichannel commerce, inventory optimization, personalized marketing, and store operations.

## Overview

This Value Pack provides pre-built value models, formulas, and workflows for Retail & Consumer business case development. It includes comprehensive definitions for omnichannel fulfillment, dynamic pricing, inventory optimization, personalized marketing, workforce management, and loss prevention.

## Pack Contents

| File | Description |
|------|-------------|
| `ontology.json` | 13 entities (6 capabilities, 3 use cases, 3 personas, 3 value drivers) with 10 relationships |
| `formulas.json` | 7 retail and consumer formulas with governance metadata |

## Quick Start

### Load the Pack

```python
import json

# Load ontology
with open('packs/retail-consumer/ontology.json') as f:
    ontology = json.load(f)

# Load formulas
with open('packs/retail-consumer/formulas.json') as f:
    formulas = json.load(f)
```

### Use a Formula

```python
# Example: Calculate Omnichannel Fulfillment ROI
variables = {
    "Incremental_Revenue": 50_000_000,
    "Cost_Avoidance": 15_000_000,
    "Fulfillment_Cost_Inflation": 20_000_000,
    "Omnichannel_Investment": 30_000_000
}

net_benefit = (variables["Incremental_Revenue"] + 
               variables["Cost_Avoidance"] - 
               variables["Fulfillment_Cost_Inflation"])
roi = net_benefit / variables["Omnichannel_Investment"] * 100

print(f"Omnichannel ROI: {roi:.1f}%")

# Example: Calculate Inventory Optimization Value
inventory_vars = {
    "Stockout_Recovery": 20_000_000,
    "Working_Capital_Benefit": 15_000_000,
    "Obsolescence_Reduction": 8_000_000,
    "Optimization_Investment": 6_000_000
}

net_value = (inventory_vars["Stockout_Recovery"] + 
             inventory_vars["Working_Capital_Benefit"] + 
             inventory_vars["Obsolescence_Reduction"] - 
             inventory_vars["Optimization_Investment"])

print(f"Inventory Optimization Value: ${net_value:,.0f}")
```

## Included Formulas

| ID | Name | Type | Status | Business Driver |
|----|------|------|--------|-----------------|
| rc-f-001 | Omnichannel Fulfillment ROI | ROI | Active | Revenue Enhancement |
| rc-f-002 | Dynamic Pricing Value | Custom | Active | Profitability |
| rc-f-003 | Inventory Optimization Value | Custom | Active | Capital Efficiency |
| rc-f-004 | Personalized Marketing ROI | ROI | Active | Customer Acquisition |
| rc-f-005 | Store Labor Optimization Value | Custom | Active | Cost Reduction |
| rc-f-006 | Visual Search and Discovery Value | Custom | Draft | Conversion |
| rc-f-007 | Loss Prevention Analytics Value | Custom | Active | Risk Mitigation |

## Key Variables

### Omnichannel Metrics
- `Incremental_Revenue` - Additional revenue from omnichannel customers
- `Cost_Avoidance` - Savings from store-based fulfillment
- `Fulfillment_Cost_Inflation` - Costs from same-day and expedited delivery
- `Omnichannel_Investment` - Annual OMS and fulfillment platform investment

### Pricing Metrics
- `Margin_Improvement_Value` - Value from optimized pricing
- `Markdown_Reduction_Value` - Reduced end-of-season markdowns
- `Competitive_Position_Value` - Value from competitive positioning

### Inventory Metrics
- `Stockout_Recovery` - Recovered sales from reduced stockouts
- `Working_Capital_Benefit` - Inventory reduction value
- `Obsolescence_Reduction` - Reduced write-offs from forecasting
- `Inventory_Turns_Improvement` - Target turns improvement

### Marketing Metrics
- `Incremental_Revenue` - Additional revenue from personalization
- `Marketing_Spend_Efficiency` - Reduced spend for same results
- `Customer_Lifetime_Value_Lift` - CLV increase from personalization

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
- Omnichannel Order Management - Ship-from-store, BOPIS, same-day delivery
- Dynamic Pricing Engine - Competitive pricing and markdown optimization
- Demand Forecasting - ML-based inventory planning and replenishment
- Customer Data Platform - Personalization and journey orchestration
- Workforce Management - AI-powered scheduling and labor optimization
- Visual AI Search - Computer vision product discovery

**Use Cases:**
- Ship-from-Store - Store-based fulfillment optimization
- BOPIS - Buy online pickup in store with cross-sell
- Same-Day Delivery - Last-mile delivery from stores

**Personas:**
- Chief Merchandising Officer - Assortment, pricing, and inventory
- VP Digital Commerce - E-commerce and omnichannel experience
- VP Store Operations - Store performance and labor management

**Value Drivers:**
- Same-Store Sales Growth - Year-over-year comparable sales
- Gross Margin Rate - Profitability after markdowns
- Inventory Turns - Inventory efficiency and working capital

## Industry Benchmarks

| Metric | Best-in-Class | Average | Poor |
|--------|---------------|---------|------|
| Same-Store Sales Growth | 8% | 2% | -3% |
| Gross Margin Rate | 45% | 35% | 25% |
| Inventory Turns | 8x | 4x | 2x |
| Omnichannel Customer Lift | 30% | 15% | 5% |
| Shrink Rate | 0.8% | 1.4% | 2.5% |

## Pack Metadata

- **Pack ID:** retail-consumer-v1
- **Version:** 1.0.0
- **Industry:** Retail & Consumer / CPG / E-commerce
- **Created:** 2026-04-15

## See Also

- [Life Sciences Value Pack](../life-sciences/README.md) - Pharma/biotech reference
- [Financial Services Value Pack](../financial-services/README.md) - Banking and fintech
- [Energy & Utilities Value Pack](../energy-utilities/README.md) - Grid and renewables

## License

Internal use only - Retail & Consumer Value Engineering Team
