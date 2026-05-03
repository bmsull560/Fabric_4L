# Value Packs

## Overview

Value Packs define industry-specific ontologies, personas, signals, drivers, formulas, benchmarks, and business case templates.

## Existing Packs

The project already includes comprehensive Value Packs in `packs/`:

| Pack | Industry | Formulas | Variables | Entities |
|------|----------|----------|-----------|----------|
| software-v1 | B2B SaaS | 7 | 30 | 13 |
| manufacturing-v1 | Manufacturing | 7 | 35 | 13 |
| life-sciences-v1 | Life Sciences | 7 | 33 | 13 |
| financial-services-v1 | Financial Services | 7 | 35 | 13 |
| energy-utilities-v1 | Energy & Utilities | 7 | 34 | 13 |
| retail-consumer-v1 | Retail & Consumer | 7 | 28 | 13 |
| ai-technology-v1 | AI/ML Platforms | 7 | 28 | 13 |

## Pack Structure

Each pack contains:
- `ontology.json` - Entity types, relationships, and entity definitions
- `formulas.json` - Formula registry with inputs, outputs, and governance
- `variables.json` - Variable definitions and defaults
- `workflow_template.json` - Business case template sections
- `tests/` - Pack integrity and formula execution tests

## Integration

The unified backend (`services/api`) loads pack metadata from `packs/pack-manifest.json` into the `ValuePack` model. Formula and ontology details are served via the Context Engine endpoints.

## Usage

1. Assign a Value Pack to an Account during setup
2. Ontology Match tab shows matched drivers and formulas
3. Hypothesis generation uses pack personas and signal patterns
4. ROI Calculator uses pack formulas and benchmarks
5. Business Case generation uses pack templates
