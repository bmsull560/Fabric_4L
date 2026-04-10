# Value Pack Authoring Guide

## Overview

Value Packs are reusable, industry-specific value models that accelerate business case development. This guide explains how to create, structure, and validate Value Packs for the Value Fabric Platform.

## What is a Value Pack?

A Value Pack contains:
- **Ontology:** Industry-specific entities (capabilities, use cases, personas, value drivers)
- **Formulas:** Pre-built ROI and value calculation formulas
- **Variables:** Pre-configured variable definitions with source bindings
- **Workflow Templates:** Step-by-step business case workflows

## Pack Structure

```
packs/{pack_name}/
├── ontology.json          # Entity definitions and relationships
├── formulas.json          # Value calculation formulas
├── variables.json         # Variable catalog
├── workflow_template.json # Business case workflow
└── README.md             # Pack documentation
```

## Pack Manifest

Each pack must include a pack manifest at the top of each JSON file:

```json
{
  "pack_id": "{industry}-v{version}",
  "pack_name": "{Industry} Value Pack",
  "version": "{semver}",
  "description": "...",
  "industry": "{industry_vertical}",
  "created_at": "YYYY-MM-DD"
}
```

## Creating an Ontology

The ontology defines your industry's value tree structure:

```json
{
  "ontology": {
    "node_types": {
      "Capability": {
        "description": "...",
        "examples": ["..."]
      },
      "UseCase": {
        "description": "...",
        "examples": ["..."]
      },
      "Persona": {
        "description": "...",
        "examples": ["..."]
      },
      "ValueDriver": {
        "description": "...",
        "examples": ["..."]
      }
    },
    "relationships": {
      "ENABLES": { "from": "Capability", "to": "UseCase" },
      "BENEFITS": { "from": "UseCase", "to": "Persona" },
      "DRIVES": { "from": "Persona", "to": "ValueDriver" }
    }
  },
  "entities": [...],
  "relationships": [...]
}
```

### Entity Guidelines

**Capabilities:**
- Must map to real technologies or processes
- Include technical specifications
- Link to at least one use case

**Use Cases:**
- Describe specific operational scenarios
- Include automation level (FULLY_AUTOMATED, SEMI_AUTOMATED, ASSISTED, MANUAL)
- Must benefit at least one persona

**Personas:**
- Define decision-making authority
- Include pain points and success metrics
- Must drive at least one value driver

**Value Drivers:**
- Categorize as REVENUE_ENHANCEMENT, COST_REDUCTION, RISK_MITIGATION, or CAPITAL_EFFICIENCY
- Include quantification method (FORMULA, BENCHMARK, ESTIMATED, QUALITATIVE)
- Provide typical value ranges

## Creating Formulas

Formulas define how value is calculated:

```json
{
  "formula_id": "{pack_prefix}-f-{number}",
  "name": "...",
  "description": "...",
  "formula_type": "ROI|NPV|IRR|CUSTOM|BENCHMARK",
  "version": "{semver}",
  "status": "draft|active|deprecated",
  "governance": {
    "owner": "...",
    "review_cycle": "quarterly|annual",
    "approval_status": "pending_review|approved",
    "last_reviewed": "YYYY-MM-DD",
    "validated_by": "..."
  },
  "expression": {
    "format": "STRING_EXPRESSION",
    "string": "{formula_expression}",
    "variables": ["var1", "var2", "..."]
  },
  "required_variables": [...]
}
```

### Formula Best Practices

1. **Use clear variable names:** `Current_OEE` not `c_oee`
2. **Provide defaults:** Every variable should have a reasonable default
3. **Validate ranges:** Define valid min/max values
4. **Document sources:** Indicate where variable data comes from
5. **Version control:** Increment version for any formula changes

### Formula Expression Syntax

Use standard mathematical notation with curly braces for variables:

```
(({Current_OEE} - {Baseline_OEE}) / 100) * {Annual_Production_Value}
```

Supported operators:
- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Logical: `AND`, `OR`, `NOT`
- Functions: `SUM()`, `AVG()`, `MIN()`, `MAX()`, `IF()`

## Creating Variables

Variables define the data inputs for formulas:

```json
{
  "variable_id": "{pack_prefix}-var-{number}",
  "variable_name": "Variable_Name",
  "display_name": "Human Readable Name",
  "description": "...",
  "data_type": "INTEGER|FLOAT|CURRENCY|PERCENTAGE|BOOLEAN|STRING",
  "unit_of_measure": "%|USD|hours|units|...",
  "valid_range": { "min": 0, "max": 100 },
  "default_value": 75.0,
  "source_type": "USER_INPUT|DERIVED|BENCHMARK|LOOKUP",
  "source_binding": {
    "system": "MES|ERP|CRM|...",
    "entity": "...",
    "attribute": "...",
    "refresh_frequency": "realtime|hourly|daily"
  }
}
```

### Data Types

| Type | Description | Example |
|------|-------------|---------|
| INTEGER | Whole numbers | `1000` |
| FLOAT | Decimal numbers | `75.5` |
| CURRENCY | Monetary values | `50000.00` |
| PERCENTAGE | 0-100 values | `85.0` |
| BOOLEAN | True/False | `true` |
| STRING | Text | `"Active"` |

### Source Types

**USER_INPUT:** Manual entry required
**DERIVED:** Calculated from other variables
**BENCHMARK:** Industry benchmark value
**LOOKUP:** Retrieved from external system

## Creating Workflow Templates

Workflows define the business case creation process:

```json
{
  "template_id": "{pack_prefix}-wf-{number}",
  "template_name": "...",
  "description": "...",
  "estimated_duration": "2-3 weeks",
  "required_roles": ["analyst", "value_engineer"],
  "phases": [
    {
      "phase_id": "discovery",
      "name": "Discovery & Data Collection",
      "order": 1,
      "tasks": [...]
    }
  ]
}
```

### Task Structure

```json
{
  "task_id": "{phase_prefix}-{number}",
  "name": "Task Name",
  "description": "...",
  "type": "data_collection|value_calculation|validation|recommendation|documentation|review|approval",
  "priority": "high|medium|low",
  "assigned_role": "analyst|value_engineer|...",
  "estimated_hours": 4,
  "dependencies": ["task-id-1", "task-id-2"],
  "input_variables": ["var1", "var2"],
  "formulas_used": ["formula-id-1"],
  "automated_data_sources": ["MES", "ERP"],
  "manual_inputs_required": [...],
  "deliverables": [...]
}
```

## Validation and Testing

### Pack Validation Checklist

- [ ] All JSON files are valid JSON
- [ ] All IDs follow naming convention: `{pack_prefix}-{type}-{number}`
- [ ] All formulas reference existing variables
- [ ] All variables have valid data types
- [ ] All relationships connect existing entities
- [ ] Governance metadata is complete for all formulas
- [ ] Benchmark references are industry-appropriate

### Formula Testing

Test formulas with boundary values:

```json
{
  "test_cases": [
    {
      "name": "Minimum values",
      "inputs": { "var1": 0, "var2": 0 },
      "expected_result": 0
    },
    {
      "name": "Maximum values",
      "inputs": { "var1": 100, "var2": 1000000 },
      "expected_result": 100000000
    },
    {
      "name": "Typical scenario",
      "inputs": { "var1": 50, "var2": 500000 },
      "expected_result": 25000000
    }
  ]
}
```

### Pack Testing Framework

Include a test configuration:

```json
{
  "test_config": {
    "unit_tests": [
      {
        "target": "formula",
        "id": "mfg-f-001",
        "test_cases": "..."
      }
    ],
    "integration_tests": [
      {
        "target": "workflow",
        "id": "mfg-wf-001",
        "scenario": "typical_manufacturing_assessment"
      }
    ],
    "validation_tests": [
      {
        "target": "ontology",
        "check": "relationship_integrity"
      }
    ]
  }
}
```

## Governance and Quality Standards

### Formula Governance

All formulas must include:
- Clear ownership
- Review cycle definition
- Approval workflow
- Version history
- Validation evidence

### Variable Governance

Variables must be:
- Named consistently (Pascal_Snake_Case)
- Properly typed
- Sourced appropriately
- Validated with ranges
- Documented with descriptions

### Version Control

Follow semantic versioning:
- `MAJOR`: Breaking changes to formulas or variables
- `MINOR`: New formulas, non-breaking additions
- `PATCH`: Bug fixes, documentation updates

## Publishing a Pack

1. **Quality Review:**
   - Technical accuracy review
   - Business value validation
   - Documentation completeness

2. **Testing:**
   - Unit test all formulas
   - Integration test workflows
   - Validate with sample data

3. **Documentation:**
   - Create README with usage examples
   - Document all assumptions
   - Provide getting started guide

4. **Submission:**
   - Submit to pack registry
   - Include metadata and tags
   - Define supported industries

## Example: Manufacturing Pack

See `packs/manufacturing/` for a complete reference implementation including:
- 10 entities (capabilities, use cases, personas, value drivers)
- 7 formulas covering OEE, maintenance, quality, and energy
- 15 variables with MES/ERP/CMMS source bindings
- 1 complete workflow template with 5 phases

## Best Practices

1. **Start Simple:** Begin with 3-5 core formulas
2. **Validate Assumptions:** Test formulas with real customer data
3. **Document Everything:** Include rationale for all assumptions
4. **Benchmark Appropriately:** Use industry-standard benchmarks
5. **Iterate:** Gather feedback and refine formulas
6. **Version Control:** Track all changes with semantic versions
7. **Test Thoroughly:** Include edge cases and boundary conditions

## Support

For questions or issues:
- Review existing packs for patterns
- Check formula syntax against examples
- Validate JSON structure with schema
- Contact the Value Engineering team
