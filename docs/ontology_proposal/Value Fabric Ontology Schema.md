# Value Fabric Ontology Schema
## Canonical Knowledge Representation

**Version:** 1.0.0  
**Status:** PRODUCTION DESIGN  
**Date:** April 2026

---

## 1. Design Philosophy

The Value Fabric Ontology Schema defines the canonical knowledge representation of a vendor's value system. It serves as the single source of truth for all entities extracted from unstructured text, ensuring consistency across the entire platform.

### The Problem This Solves
Historically, different agents and components used varying schemas (e.g., `label` vs `name`, `type` vs `entity_type`). This schema drift required runtime translation and frontend compensation logic. By enforcing a canonical `EntityRef` schema, we eliminate this technical debt and enable strict, compile-time type checking across all agent boundaries.

---

## 2. Canonical Entity Reference (`EntityRef`)

The `EntityRef` is the foundational building block of the Value Fabric ontology. It replaces all ad-hoc IDs and labels.

```typescript
export interface EntityRef {  
  id: string;                    // UUID v4  
  canonicalName: string;         // The single, normalized name  
  entityType: EntityType;        // The canonical entity type  
  source: SourceType;            // Origin of the entity  
  provenance: ProvenanceChain;   // Traceability metadata  
  confidence: ConfidenceScore;   // Reliability metric  
}
```

### 2.1. Entity Types (`EntityType`)

The ontology supports 57 distinct entity types, categorized into core domains:

*   **Primary Business Concepts:** `Capability`, `UseCase`, `Persona`, `ValueDriver`, `ValueMetric`
*   **Product & Solution Domain:** `Product`, `Feature`, `Service`, `Solution`, `Technology`
*   **Organizational Context:** `Organization`, `BusinessUnit`, `Process`, `Activity`
*   **Supporting Concepts:** `Industry`, `MarketSegment`, `Geography`, `Regulation`
*   **Metadata & Provenance:** `DataSource`, `ExtractionEvent`, `ConfidenceScore`

### 2.2. Source Types (`SourceType`)

*   `WEBSITE_EXTRACTED`
*   `CRM_IMPORT`
*   `USER_INPUT`
*   `INFERRED`
*   `BENCHMARK`
*   `ANALYST_REPORT`

---

## 3. Core Relationships

The ontology defines strict relationships between entity types, enabling the construction of a robust knowledge graph.

| Relationship | Domain | Range | Description |
| :--- | :--- | :--- | :--- |
| `enables` | `Capability` | `UseCase` | A capability provides the technical foundation for a use case. |
| `delivers` | `UseCase` | `ValueDriver` | Executing a use case results in a specific business value. |
| `impacts` | `ValueDriver` | `ValueMetric` | A value driver measurably affects a specific KPI. |
| `involves` | `UseCase` | `Persona` | A persona participates in or benefits from a use case. |
| `implements` | `Feature` | `Capability` | A product feature realizes a specific capability. |

---

## 4. Provenance and Confidence

Every entity in the Value Fabric ontology must maintain strict lineage and confidence scoring.

### 4.1. Provenance Chain

```typescript
export interface ProvenanceChain {  
  originUrl?: string;  
  extractionTimestamp: ISO8601Timestamp;  
  extractorVersion: string;  
  llmModel?: string;  
  humanReviewed: boolean;  
  reviewDate?: ISO8601Timestamp;  
}
```

### 4.2. Confidence Score

```typescript
export interface ConfidenceScore {  
  score: number;                 // 0.0 - 1.0  
  baseWeight: number;            // Page-type authority  
  claimTypeMultiplier: number;   // EXPLICIT_METRIC = 1.0, etc.  
  corroborationBonus: number;    // 0.0, 0.10, 0.15  
  temporalPenalty: number;       // 0.0, -0.05, -0.10, -0.15  
  governanceFlags: GovernanceFlag[];  
}
```

---

## 5. Implementation Guidelines

1.  **Strict Enforcement:** The `EntityRef` schema MUST be enforced at every agent boundary and frontend interface using the `SchemaValidator`.
2.  **No Runtime Translation:** Agents MUST NOT translate between legacy fields (e.g., `label`, `name`) and canonical fields (`canonicalName`). The `CANONICAL_FIELD_MAP` is for one-time migration only.
3.  **Graph Alignment:** The Neo4j ingestion pipeline MUST populate nodes using the exact `EntityRef` structure.
