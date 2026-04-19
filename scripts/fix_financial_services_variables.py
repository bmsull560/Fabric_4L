#!/usr/bin/env python3
"""Fix missing variables in financial-services pack."""

import json
from pathlib import Path

def main():
    packs_dir = Path('packs')
    variables_path = packs_dir / 'financial-services' / 'variables.json'
    manifest_path = packs_dir / 'pack-manifest.json'

    with open(variables_path) as f:
        data = json.load(f)

    variables = data['variables']
    existing_vars = {v['variable_name'] for v in variables}

    # Missing variables needed by formulas
    missing_vars = [
        {
            "variable_id": "fs-var-020",
            "variable_name": "Expanded_Lending_Profit",
            "display_name": "Expanded Lending Profit",
            "description": "Additional profit from expanded lending to previously underserved segments",
            "data_type": "CURRENCY",
            "unit_of_measure": "USD",
            "valid_range": {"min": 0, "max": 100000000},
            "default_value": 5000000,
            "source_type": "USER_INPUT",
            "validation_rules": [{"type": "range", "min": 0, "max": 100000000}],
            "tags": ["lending", "profit", "expansion", "credit"],
            "used_in_formulas": ["fs-f-003"]
        },
        {
            "variable_id": "fs-var-021",
            "variable_name": "Model_Investment",
            "display_name": "Credit Model Investment",
            "description": "Annual investment in credit risk models, data, and ML infrastructure",
            "data_type": "CURRENCY",
            "unit_of_measure": "USD",
            "valid_range": {"min": 0, "max": 20000000},
            "default_value": 3000000,
            "source_type": "USER_INPUT",
            "validation_rules": [{"type": "range", "min": 0, "max": 20000000}],
            "tags": ["model", "investment", "credit", "ml"],
            "used_in_formulas": ["fs-f-003"]
        },
        {
            "variable_id": "fs-var-022",
            "variable_name": "Avoided_Findings_Cost",
            "display_name": "Avoided Regulatory Findings Cost",
            "description": "Cost avoidance from reduced regulatory findings and enforcement actions",
            "data_type": "CURRENCY",
            "unit_of_measure": "USD",
            "valid_range": {"min": 0, "max": 50000000},
            "default_value": 8000000,
            "source_type": "USER_INPUT",
            "validation_rules": [{"type": "range", "min": 0, "max": 50000000}],
            "tags": ["regulatory", "findings", "compliance", "avoidance"],
            "used_in_formulas": ["fs-f-004"]
        },
        {
            "variable_id": "fs-var-023",
            "variable_name": "Automation_Platform_Cost",
            "display_name": "Compliance Automation Platform Cost",
            "description": "Annual cost of compliance automation platform and operations",
            "data_type": "CURRENCY",
            "unit_of_measure": "USD",
            "valid_range": {"min": 0, "max": 20000000},
            "default_value": 4000000,
            "source_type": "USER_INPUT",
            "validation_rules": [{"type": "range", "min": 0, "max": 20000000}],
            "tags": ["compliance", "automation", "platform", "cost"],
            "used_in_formulas": ["fs-f-004"]
        },
        {
            "variable_id": "fs-var-024",
            "variable_name": "Customer_Base",
            "display_name": "Active Customer Base",
            "description": "Number of active customers eligible for personalization",
            "data_type": "INTEGER",
            "unit_of_measure": "customers",
            "valid_range": {"min": 0, "max": 10000000},
            "default_value": 500000,
            "source_type": "LOOKUP",
            "source_binding": {
                "system": "CRM",
                "entity": "CustomerSegment",
                "attribute": "active_count",
                "refresh_frequency": "daily"
            },
            "validation_rules": [{"type": "range", "min": 0, "max": 10000000}],
            "tags": ["customers", "base", "personalization"],
            "used_in_formulas": ["fs-f-005"]
        },
        {
            "variable_id": "fs-var-025",
            "variable_name": "Personalization_Uplift_Rate",
            "display_name": "Personalization Revenue Uplift Rate",
            "description": "Percentage revenue uplift from personalized offers and recommendations",
            "data_type": "RATE",
            "unit_of_measure": "percent",
            "valid_range": {"min": 0, "max": 0.5},
            "default_value": 0.05,
            "source_type": "USER_INPUT",
            "validation_rules": [{"type": "range", "min": 0, "max": 0.5}],
            "tags": ["personalization", "uplift", "revenue", "rate"],
            "used_in_formulas": ["fs-f-005"]
        },
        {
            "variable_id": "fs-var-026",
            "variable_name": "Avg_Revenue_Per_Customer",
            "display_name": "Average Revenue Per Customer",
            "description": "Average annual revenue per customer",
            "data_type": "CURRENCY",
            "unit_of_measure": "USD",
            "valid_range": {"min": 0, "max": 10000},
            "default_value": 250,
            "source_type": "DERIVED",
            "derivation": {"formula": "Total_Revenue / Customer_Base"},
            "validation_rules": [{"type": "range", "min": 0, "max": 10000}],
            "tags": ["revenue", "customer", "average", "arpu"],
            "used_in_formulas": ["fs-f-005"]
        },
        {
            "variable_id": "fs-var-027",
            "variable_name": "Personalization_Platform_Cost",
            "display_name": "Personalization Platform Cost",
            "description": "Annual cost of personalization platform and data",
            "data_type": "CURRENCY",
            "unit_of_measure": "USD",
            "valid_range": {"min": 0, "max": 20000000},
            "default_value": 5000000,
            "source_type": "USER_INPUT",
            "validation_rules": [{"type": "range", "min": 0, "max": 20000000}],
            "tags": ["personalization", "platform", "cost"],
            "used_in_formulas": ["fs-f-005"]
        },
        {
            "variable_id": "fs-var-028",
            "variable_name": "Settlement_Failure_Cost_Avoidance",
            "display_name": "Settlement Failure Cost Avoidance",
            "description": "Cost avoidance from reduced settlement failures",
            "data_type": "CURRENCY",
            "unit_of_measure": "USD",
            "valid_range": {"min": 0, "max": 20000000},
            "default_value": 5000000,
            "source_type": "USER_INPUT",
            "validation_rules": [{"type": "range", "min": 0, "max": 20000000}],
            "tags": ["settlement", "failure", "avoidance", "operations"],
            "used_in_formulas": ["fs-f-006"]
        },
        {
            "variable_id": "fs-var-029",
            "variable_name": "Capital_Efficiency_Value",
            "display_name": "Capital Efficiency Value",
            "description": "Value from improved capital efficiency and reduced funding costs",
            "data_type": "CURRENCY",
            "unit_of_measure": "USD",
            "valid_range": {"min": 0, "max": 20000000},
            "default_value": 3000000,
            "source_type": "USER_INPUT",
            "validation_rules": [{"type": "range", "min": 0, "max": 20000000}],
            "tags": ["capital", "efficiency", "funding", "value"],
            "used_in_formulas": ["fs-f-006"]
        },
        {
            "variable_id": "fs-var-030",
            "variable_name": "STP_Investment",
            "display_name": "Straight-Through Processing Investment",
            "description": "Annual investment in STP and settlement automation",
            "data_type": "CURRENCY",
            "unit_of_measure": "USD",
            "valid_range": {"min": 0, "max": 15000000},
            "default_value": 4000000,
            "source_type": "USER_INPUT",
            "validation_rules": [{"type": "range", "min": 0, "max": 15000000}],
            "tags": ["stp", "settlement", "investment", "automation"],
            "used_in_formulas": ["fs-f-006"]
        },
        {
            "variable_id": "fs-var-031",
            "variable_name": "Additional_Clients_Per_Advisor",
            "display_name": "Additional Clients Per Advisor",
            "description": "Additional clients each advisor can serve with AI tools",
            "data_type": "INTEGER",
            "unit_of_measure": "clients",
            "valid_range": {"min": 0, "max": 100},
            "default_value": 25,
            "source_type": "USER_INPUT",
            "validation_rules": [{"type": "range", "min": 0, "max": 100}],
            "tags": ["advisor", "clients", "capacity", "ai"],
            "used_in_formulas": ["fs-f-007"]
        },
        {
            "variable_id": "fs-var-032",
            "variable_name": "Advisor_Count",
            "display_name": "Advisor Count",
            "description": "Total number of wealth management advisors",
            "data_type": "INTEGER",
            "unit_of_measure": "advisors",
            "valid_range": {"min": 0, "max": 10000},
            "default_value": 500,
            "source_type": "LOOKUP",
            "source_binding": {
                "system": "HRIS",
                "entity": "Employee",
                "attribute": "headcount",
                "refresh_frequency": "monthly"
            },
            "validation_rules": [{"type": "range", "min": 0, "max": 10000}],
            "tags": ["advisor", "count", "headcount", "wealth"],
            "used_in_formulas": ["fs-f-007"]
        },
        {
            "variable_id": "fs-var-033",
            "variable_name": "Performance_Uplift_Value",
            "display_name": "Advisor Performance Uplift Value",
            "description": "Value from improved advisor performance with AI assistance",
            "data_type": "CURRENCY",
            "unit_of_measure": "USD",
            "valid_range": {"min": 0, "max": 50000000},
            "default_value": 8000000,
            "source_type": "USER_INPUT",
            "validation_rules": [{"type": "range", "min": 0, "max": 50000000}],
            "tags": ["advisor", "performance", "uplift", "ai"],
            "used_in_formulas": ["fs-f-007"]
        },
        {
            "variable_id": "fs-var-034",
            "variable_name": "AI_Tools_Investment",
            "display_name": "AI Tools Investment",
            "description": "Annual investment in AI tools for wealth advisors",
            "data_type": "CURRENCY",
            "unit_of_measure": "USD",
            "valid_range": {"min": 0, "max": 15000000},
            "default_value": 3000000,
            "source_type": "USER_INPUT",
            "validation_rules": [{"type": "range", "min": 0, "max": 15000000}],
            "tags": ["ai", "tools", "investment", "wealth"],
            "used_in_formulas": ["fs-f-007"]
        }
    ]

    # Add missing variables with canonicalName and name
    added_count = 0
    existing_ids = {v['variable_id'] for v in variables}
    
    for var in missing_vars:
        if var['variable_name'] not in existing_vars:
            # Check for ID collision
            if var['variable_id'] in existing_ids:
                print(f"⚠️  Skipping {var['variable_name']}: ID '{var['variable_id']}' already exists")
                continue
            
            var['canonicalName'] = var['variable_name']
            var['name'] = var['display_name']
            variables.append(var)
            existing_ids.add(var['variable_id'])
            added_count += 1
            print(f"Added: {var['variable_name']} ({var['variable_id']})")

    # Save variables.json
    with open(variables_path, 'w') as f:
        json.dump(data, f, indent=2)

    # Update manifest
    with open(manifest_path) as f:
        manifest = json.load(f)

    for pack in manifest['packs']:
        if pack['pack_id'] == 'financial-services-v1':
            old_count = pack['variable_count']
            pack['variable_count'] = len(variables)
            print(f"\nUpdated financial-services: {old_count} -> {pack['variable_count']} variables")
            break

    # Recalculate total
    total_vars = sum(p['variable_count'] for p in manifest['packs'])
    manifest['statistics']['total_variables'] = total_vars
    print(f"Total variables in manifest: {total_vars}")

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n✅ Added {added_count} missing variables")

if __name__ == '__main__':
    main()
