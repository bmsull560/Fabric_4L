# Value Fabric Architecture Integration Guide
## How the Four Documents Form a Coherent System

**Version:** 1.0.0  
**Date:** April 2026

---

## 1. The Problem This Solves

The system previously had **implicit agents without explicit contracts**, leading to several issues:

| Symptom | Root Cause |
|---------|-----------|
| `test_pack_variables_loadable` failing | No agent owned the Variable Registry |
| `test_formula_variable_references_valid` failing | Formulas referenced variables that weren't validated against an authoritative source |
| `test_manifest_variable_counts` failing | Pack-defined variables and formula references had no reconciliation layer |
| `label` vs `name` vs `canonicalName` drift | No canonical Entity Schema enforced across agents |
| Frontend compensating for backend inconsistency | UI acting as adapter for broken contracts |
| Schema drift (GraphNode mismatch) | No typed artifact boundaries between agent responsibilities |

These were not bugs. They were **symptoms of a missing architectural layer**.

---

## 2. The Four-Document Architecture

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                    DOCUMENT 1: ONTOLOGY SCHEMA                            │
│                    (Value_Fabric_Ontology_Schema.md)                      │
│                                                                           │
│  WHAT exists: 57 entity types, 50 relationships, 82 normalization rules  │
│  PURPOSE: Canonical knowledge representation of a vendor's value system  │
│  CONSUMED BY: ContextExtractionAgent → populates ContextArtifact         │
│               ValueModelAgent → builds capability-value chains           │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ produces entities
┌──────────────────────────────────────────────────────────────────────────┐
│                    DOCUMENT 2: SYSTEM ARCHITECTURE                        │
│                    (Value_Fabric_System_Architecture.md)                  │
│                                                                           │
│  WHAT exists: Dual-path ingestion (HTTPX + Stagehand), Neo4j pipeline    │
│  PURPOSE: How raw website content becomes structured ontology in graph   │
│  OUTPUTS: Populates Neo4j with entities + relationships                  │
│  CONSUMED BY: ContextExtractionAgent → reads product ontology from Neo4j │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ entities in graph
┌──────────────────────────────────────────────────────────────────────────┐
│                    DOCUMENT 3: AGENT SKILL ARCHITECTURE                   │
│                    (Value_Fabric_Agent_Skill_Architecture.md)             │
│                                                                           │
│  WHAT exists: 14 skills in 5 layers, 3-agent hybrid design               │
│  PURPOSE: How agents reason about value from discovery to narrative      │
│  DEFINES: Which agent does what, but NOT how they exchange data          │
│  GAP: No typed contracts between agents                                  │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ THE MISSING PIECE
┌──────────────────────────────────────────────────────────────────────────┐
│                    DOCUMENT 4: ARTIFACT CONTRACTS  ◄── NEW               │
│                    (Value_Fabric_Artifact_Contracts.md)                   │
│                                                                           │
│  WHAT exists: 4 canonical artifacts as TypeScript interfaces             │
│  PURPOSE: Typed boundaries between agents — eliminates drift             │
│  FIXES: Variable Registry, schema enforcement, broken test triad         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. The Four Canonical Artifacts

| Artifact | Owner | Consumers | Resolves |
|----------|-------|-----------|----------|
| **ContextArtifact** | ContextExtractionAgent | ValueModelAgent | Discovery notes → structured context; stakeholder mapping; pain point clustering |
| **ValueModelArtifact** | ValueModelAgent | IntegrityAgent, NarrativeAgent | The bridge (capability → use case → outcome); Variable Registry; financial model |
| **IntegrityArtifact** | IntegrityAgent | ValueModelAgent (feedback), NarrativeAgent | Independent challenge; assumption audit; evidence scoring; defensibility review |
| **NarrativeArtifact** | NarrativeAgent | End user (UI) | Executive summary; stakeholder versions; objection briefs; realization plan |

---

## 4. What Changed: Before vs After

### 4.1 Variable Registry

**Before: Implicit Coordination**
Packs defined variables, loaders tried to reconcile them, and formulas referenced them without an authoritative source. This caused tests like `test_pack_variables_loadable` to fail.

**After: Explicit Variable Registry**
The `VariableRegistry` is now a mandatory component of the `ValueModelArtifact`. Pack loaders populate it, formula agents validate against it, and integrity agents audit it.

### 4.2 Schema Drift

**Before: Schema Drift**
Different agents and the frontend used varying schemas (e.g., `label` vs `name`, `type` vs `entity_type`), requiring runtime translation and frontend compensation logic.

**After: Canonical EntityRef**
All agents and the frontend use the canonical `EntityRef` schema. This enables compile-time type checking and eliminates runtime translation.

---

## 5. Migration Path

1.  **Define canonical field map (1 day):** Create a single `CANONICAL_FIELD_MAP.ts` file for one-time migration.
2.  **Implement EntityRef everywhere (2 days):** Replace ad-hoc objects with `EntityRef` and add `SchemaValidator` at boundaries.
3.  **Add VariableRegistry to ValueModelArtifact (2 days):** Make it required, update loaders, formula agents, and integrity agents.
4.  **Add SchemaValidator runtime checks (1 day):** Enforce validation at every agent boundary.
5.  **Remove frontend compensation code (1 day):** Delete translation logic in the frontend.

**Total: 7 days to eliminate the drift category entirely.**
