# Semantic Contract: Ontology ↔ Extraction ↔ Storage Mapping

This document defines the semantic contract between pack ontologies, Layer 2 extraction, and Layer 3 storage. It ensures consistent vocabulary and data flow across the Value Fabric pipeline.

## Overview

| Layer | Purpose | Key Components |
|-------|---------|----------------|
| **Pack Ontology** | Domain-specific value models | Entity types, relationships, properties |
| **L2 Extraction** | LLM-based entity/relationship extraction | Models, prompts, normalizers |
| **L3 Storage** | Knowledge Graph persistence | Neo4j schema, ingestion, retrieval |
| **L5 Ground Truth** | Evaluated truth store | TruthObjects, formulas, metrics |

## Entity Type Alignment

### Persona Model

| Concept | Pack Ontology | L2 Extraction | L3 Storage |
|---------|---------------|---------------|------------|
| Buying-process role | `role_type`: EXECUTIVE_SPONSOR, OPERATIONAL_USER, TECHNICAL_EVALUATOR | `RoleType`: economic_buyer, champion, operational_user, technical_buyer, stakeholder | `roleType` property on Persona node |
| Organizational seniority | `seniority_level`: C_SUITE, VP, DIRECTOR, MANAGER | `SeniorityLevel`: c_suite, vp, director, manager, individual_contributor, unknown | `seniorityLevel` property on Persona node |

**Key Decision**: Pack ontology and L2 extraction describe different dimensions. Pack uses seniority-based labels in `role_type`, while L2 separates `role_type` (buying function) from `seniority_level` (organizational hierarchy).

### ValueDriver Model

| Pack Category | L2 ValueCategory | L3 Storage | Notes |
|---------------|------------------|------------|-------|
| CAPITAL_EFFICIENCY | `capital_efficiency` | `category` property | Capital deployment optimization |
| COST_REDUCTION | `cost_reduction` | `category` property | Operational cost reduction |
| RISK_MITIGATION | `risk_mitigation` | `category` property | Compliance, security risk |
| REVENUE_ENHANCEMENT | `revenue_enhancement` | `category` property | Growth, retention, expansion |
| *(legacy)* | `revenue`, `cost`, `risk`, `capital` | `category` property | Backward compatibility |

## Relationship Alignment

### Core Predicates

| L2 PredicateType | Direction | L3 Relationship Type | Inverse |
|------------------|-----------|---------------------|---------|
| ENABLES | Capability → UseCase | `enables` | REQUIRES |
| REQUIRES | UseCase → Capability | `requires` | ENABLES |
| BENEFITS | UseCase → Persona | `benefits` | — |
| DRIVES | Persona → ValueDriver | `drives` | — |
| CONTRIBUTES_TO | Capability → ValueDriver | `contributesTo` | — |
| DEPENDS_ON | Capability → Capability | `dependsOn` | CAPABILITY_REQUIRES_CAPABILITY |
| ALTERNATIVE_TO | Capability → Capability | `alternativeTo` | — |

### Extended Predicates

| L2 PredicateType | Use Case |
|------------------|----------|
| CAPABILITY_SUBTYPE_OF | Capability hierarchy (parent/child) |
| CAPABILITY_REQUIRES_CAPABILITY | Capability dependency chain |
| SEMANTICALLY_EQUIVALENT | Coreference resolution |
| IMPLEMENTS | Feature delivers Capability |
| DELIVERS | UseCase produces ValueDriver outcome |
| INVOLVES | UseCase includes Persona participation |

### Relationship Properties

| Property | Applies To | Pack Ontology | L2 Model | L3 Storage |
|----------|------------|---------------|----------|------------|
| `enablement_type` | ENABLES | REQUIRED, ENHANCES, OPTIONAL | `EnablementType` | `enablement_type` relationship property |
| `benefit_type` | BENEFITS | TIME_SAVINGS, ERROR_REDUCTION, VISIBILITY, EFFICIENCY | `BenefitType` | `benefit_type` relationship property |
| `impact_level` | BENEFITS | TRANSFORMATIONAL, SIGNIFICANT, MODERATE, MINOR | `ImpactLevel` | `impact_level` relationship property |
| `driver_type` | DRIVES | PRIMARY, SECONDARY, TERTIARY | `DriverType` | `driver_type` relationship property |
| `contribution_weight` | ENABLES, CONTRIBUTES_TO | Float 0.0-1.0 | `contribution_weight` field | `contribution_weight` relationship property |
| `influence_weight` | DRIVES | Float 0.0-1.0 | `influence_weight` field | `influence_weight` relationship property |

### Raw vs. Canonical Predicates

| Raw (Extracted) | Canonical (Normalized) | Example Text |
|-----------------|-------------------------|--------------|
| "requires", "needs" | REQUIRES | "Use case requires capability" |
| "enables", "supports", "allows" | ENABLES | "Capability enables use case" |
| "benefits", "helps", "improves for" | BENEFITS | "Use case benefits persona" |
| "drives", "cares about", "prioritizes" | DRIVES | "Persona drives value driver" |
| "depends on", "needs" | DEPENDS_ON | "Capability depends on another" |

**Pattern**: L2 extraction captures rich relational language in `raw_predicate`, then normalizes to ontology-compliant `canonical_predicate` for storage.

## L2→L3→L5 Data Flow

### ValueDriver Bridge (L2→L3→L5)

```
L2 Extraction                    L3 Neo4j Storage              L5 Ground Truth
────────────────────────────────────────────────────────────────────────────────
ValueDriver {                    (ValueDriver:Node) {           TruthObject {
  category: "capital_efficiency"    category: "capital_efficiency"  category: "CAPITAL_EFFICIENCY"
  name: "Working Capital"          name: "Working Capital"         name: "Working Capital"
  formula_string: "..."             formulaString: "..."            formula: "..."
  metrics: [...]                   metrics: [...]                  metrics: [...]
  unit: "days"                     unit: "days"                    unit: "days"
}                                  }                               }
```

**Critical Path**: `formula_string` and `metrics` must flow from L2 extraction → L3 storage → L5 Ground Truth without loss.

### Relationship Property Flow

```
L2 Extraction                    RDF (Turtle)                   L3 Neo4j
────────────────────────────────────────────────────────────────────────────────
Relationship {                   vf:enables statement [         (cap)-[:enables {
  raw_predicate: "is essential"    vf:rawPredicate "is essential";   raw_predicate: "is essential",
  canonical_predicate: ENABLES     vf:enablementType "REQUIRED";     enablement_type: "REQUIRED",
  enablement_type: REQUIRED        vf:contributionWeight 0.9         contribution_weight: 0.9,
  contribution_weight: 0.9       ]                                  confidence: 0.88
  confidence: 0.88
}
```

## Extraction Prompt Alignment

### Persona Extraction

**Prompt Vocabulary** (from `persona_extraction.txt`):
```
Role Types (buying-process function):
- economic_buyer: Makes purchasing decisions
- champion: Internal advocate
- operational_user: Uses the product day-to-day
- technical_buyer: Evaluates technical fit
- stakeholder: Influenced but not direct user

Seniority Levels (organizational hierarchy):
- executive_sponsor, c_suite, vp, director, manager, individual_contributor, unknown
```

### ValueDriver Extraction

**Prompt Vocabulary** (from `valuedriver_extraction.txt`):
```
Categories (aligned with pack ontology):
- capital_efficiency: Optimizes capital deployment
- cost_reduction: Reduces operational costs
- risk_mitigation: Reduces business risk
- revenue_enhancement: Increases revenue
```

### Relationship Extraction

**Prompt Vocabulary** (from `relationship_extraction.txt`):
```
Relationship Types (raw_predicate → canonical_predicate):
- enables → ENABLES (enablement_type: REQUIRED/ENHANCES/OPTIONAL)
- requires → REQUIRES (normalized to ENABLES inverse)
- benefits → BENEFITS (benefit_type, impact_level)
- drives → DRIVES (driver_type, influence_weight)
```

## Validation Rules

### Field Presence

| Entity | Required Fields | Optional Fields |
|--------|-----------------|-----------------|
| Persona | id, role_type, title, department | seniority_level, pain_points, success_metrics |
| ValueDriver | id, category, name, description, unit | formula_string, metrics, time_to_value |
| Relationship | id, source_id, raw_predicate, canonical_predicate, target_id, evidence_text | impact_level, strength, enablement_type, benefit_type, driver_type, weights |

### Enum Validation

```python
# RoleType must be buying-process function
RoleType.ECONOMIC_BUYER  # Valid
RoleType.VP  # Invalid - use SeniorityLevel

# ValueCategory should use granular values
ValueCategory.CAPITAL_EFFICIENCY  # Preferred
ValueCategory.CAPITAL  # Legacy, still valid
```

### Predicate Normalization

```python
# Extraction returns both raw and canonical
{
    "raw_predicate": "is essential for",      # Original text
    "canonical_predicate": "enables"          # Ontology-compliant
}
```

## Testing

Run semantic contract tests:

```bash
cd value-fabric/layer2-extraction
pytest tests/test_ontology_alignment.py -v
```

Test coverage:
- Enum value alignment (RoleType, SeniorityLevel, ValueCategory)
- Relationship property enums (EnablementType, BenefitType, DriverType, ImpactLevel)
- Predicate normalization rules
- Pack ontology compatibility (life-sciences, manufacturing, software)
- End-to-end field preservation

## Change Management

When modifying this contract:

1. **Pack Ontology Changes**: Update `packs/*/ontology.json` first
2. **L2 Model Changes**: Update `value-fabric/layer2-extraction/src/models/`
3. **Prompt Changes**: Update `value-fabric/layer2-extraction/src/extraction/prompts/`
4. **L3 Schema Changes**: Update `value-fabric/layer3-knowledge/src/`
5. **Test Updates**: Update `tests/test_ontology_alignment.py`
6. **Documentation**: Update this file

Backward compatibility: Legacy enum values are preserved but marked deprecated in documentation.
