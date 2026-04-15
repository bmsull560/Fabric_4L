# Energy & Utilities Value Pack

Complete value model for utilities, renewable energy, and oil & gas - grid modernization, demand response, energy storage, and customer engagement.

## Overview

This Value Pack provides pre-built value models, formulas, and workflows for Energy & Utilities business case development. It includes comprehensive definitions for smart grid infrastructure, renewable integration, demand response programs, predictive maintenance, and energy storage.

## Pack Contents

| File | Description |
|------|-------------|
| `ontology.json` | 13 entities (5 capabilities, 3 use cases, 3 personas, 3 value drivers) with 10 relationships |
| `formulas.json` | 7 energy and utilities formulas with governance metadata |

## Quick Start

### Load the Pack

```python
import json

# Load ontology
with open('packs/energy-utilities/ontology.json') as f:
    ontology = json.load(f)

# Load formulas
with open('packs/energy-utilities/formulas.json') as f:
    formulas = json.load(f)
```

### Use a Formula

```python
# Example: Calculate Grid Modernization ROI
variables = {
    "Outage_Cost_Savings": 40_000_000,
    "Operational_Savings": 15_000_000,
    "Deferred_Capex_Value": 50_000_000,
    "Annual_Smart_Grid_Cost": 20_000_000,
    "Cumulative_Investment": 200_000_000
}

total_benefit = (variables["Outage_Cost_Savings"] + 
                 variables["Operational_Savings"] + 
                 variables["Deferred_Capex_Value"] - 
                 variables["Annual_Smart_Grid_Cost"])
roi = total_benefit / variables["Cumulative_Investment"] * 100

print(f"Grid Modernization ROI: {roi:.1f}%")

# Example: Calculate Renewable Integration Value
renewable_vars = {
    "REC_Revenue": 25_000_000,
    "Carbon_Credit_Value": 15_000_000,
    "Fuel_Cost_Savings": 80_000_000,
    "Capacity_Payment_Avoidance": 20_000_000,
    "Integration_Costs": 30_000_000
}

total_value = (renewable_vars["REC_Revenue"] + 
               renewable_vars["Carbon_Credit_Value"] + 
               renewable_vars["Fuel_Cost_Savings"] + 
               renewable_vars["Capacity_Payment_Avoidance"] - 
               renewable_vars["Integration_Costs"])

print(f"Renewable Integration Value: ${total_value:,.0f}")
```

## Included Formulas

| ID | Name | Type | Status | Business Driver |
|----|------|------|--------|-----------------|
| eu-f-001 | Grid Modernization ROI | ROI | Active | Reliability |
| eu-f-002 | Renewable Energy Integration Value | Custom | Active | Sustainability |
| eu-f-003 | Demand Response Program Value | Custom | Active | Capacity Efficiency |
| eu-f-004 | Predictive Asset Maintenance Value | Custom | Active | Reliability |
| eu-f-005 | Energy Storage Arbitrage Value | Custom | Draft | Revenue |
| eu-f-006 | Customer Engagement Platform Value | Custom | Active | Cost Reduction |
| eu-f-007 | Electric Vehicle Charging Infrastructure Value | Custom | Draft | Customer Growth |

## Key Variables

### Grid Operations Metrics
- `Outage_Cost_Savings` - Savings from reduced SAIDI/SAIFI
- `Operational_Savings` - Reduced truck rolls and automated switching
- `Deferred_Capex_Value` - Deferral of traditional infrastructure
- `Cumulative_Investment` - Total smart grid capital deployed

### Renewable Energy Metrics
- `REC_Revenue` - Renewable Energy Credit sales
- `Carbon_Credit_Value` - Carbon offset market value
- `Fuel_Cost_Savings` - Avoided fossil fuel purchases
- `Capacity_Payment_Avoidance` - Reduced capacity market obligations

### Demand Response Metrics
- `Capacity_Market_Revenue` - DR participation in capacity markets
- `Energy_Market_Revenue` - Price-based demand reduction value
- `Ancillary_Services_Revenue` - Frequency regulation payments
- `Infrastructure_Deferral` - Avoided transmission investment

### Asset Management Metrics
- `Avoided_Failure_Cost` - Prevented catastrophic failure costs
- `Extended_Life_Value` - Value from asset life extension
- `Predictive_Maintenance_Investment` - Annual PM program costs

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
- Smart Grid Platform - AMI, distribution automation, and ADMS
- Renewable Energy Management - Forecasting and grid integration
- Demand Response System - Load control and price signals
- Predictive Asset Analytics - ML-based failure prediction
- Energy Storage Control - Battery arbitrage and grid services

**Use Cases:**
- Outage Management - Rapid detection and automated restoration
- Renewable Integration - High penetration solar/wind management
- Peak Load Management - Active demand and storage dispatch

**Personas:**
- VP Grid Operations - Distribution reliability and outage management
- Director of Renewable Strategy - Clean energy goals and carbon reduction
- Asset Management Lead - Capital planning and lifecycle optimization

**Value Drivers:**
- SAIDI - System Average Interruption Duration Index
- Renewable Penetration - Percentage of generation from renewables
- Peak Demand Reduction - MW reduction through DR and efficiency

## Industry Benchmarks

| Metric | Best-in-Class | Average | Poor |
|--------|---------------|---------|------|
| SAIDI | 60 min | 180 min | 300 min |
| Renewable Penetration | 70% | 20% | 10% |
| Peak Demand Reduction | 15% | 8% | 3% |
| Asset Health Index | 85 | 70 | 55 |

## Pack Metadata

- **Pack ID:** energy-utilities-v1
- **Version:** 1.0.0
- **Industry:** Energy & Utilities / Electric / Gas / Renewables
- **Created:** 2026-04-15

## See Also

- [Life Sciences Value Pack](../life-sciences/README.md) - Pharma/biotech reference
- [Financial Services Value Pack](../financial-services/README.md) - Banking and fintech
- [Retail & Consumer Value Pack](../retail-consumer/README.md) - Omnichannel commerce

## License

Internal use only - Energy & Utilities Value Engineering Team
