# Value Fabric Agent Skill Architecture
## Formal Skill Matrix, Hybrid Agent Design & Capability Stack

**Version:** 1.0.0  
**Status:** PRODUCTION DESIGN  
**Date:** April 2026

---

## 1. Design Philosophy

### The Golden Rule

> **The agent never outputs value without showing the bridge between product use, operational change, and financial impact.**

That bridge — `Use → Operation → Outcome → Financial Impact` — is what makes a value model credible, defensible, and reusable.

### Multi-Skill vs Multi-Agent: The Hybrid Decision

After analysis of both patterns, Value Fabric uses a **hybrid architecture**:

| Pattern | When to Use | Value Fabric Choice |
|---------|------------|----------------|
| Single multi-skill agent | Linear workflow, tight coupling, consistency-first | **Primary Value Model Agent** — user-facing, coherent |
| Multi-agent system | Needs critique, governance, independent scoring | **3 Specialist Agents** — behind the scenes, rigorous |

**The rule**: Start with one multi-skill primary. Add specialists only where independence, rigor, or different reasoning modes clearly improve value quality.

### The Three-Agent Design

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                                │
│                    (single point of interaction)                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
              ┌─────────────────┴──────────────────┐
              │     PRIMARY: VALUE MODEL AGENT       │
              │     (multi-skill, coherent UX)       │
              │                                      │
              │  Skills:                             │
              │  - Business Context Extraction       │
              │  - Value Driver Identification       │
              │  - Use Case → Value Mapping          │
              │  - KPI Selection                     │
              │  - Financial Modeling                │
              │  - Assumption Registry               │
              │  - Stakeholder Tailoring             │
              │  - Industry/Persona Adaptation       │
              │  - Scenario & Sensitivity            │
              │  - Narrative Composition             │
              │                                      │
              │  Working memory, context continuity  │
              │  Traceable lineage maintained here   │
              └──────────┬───────────────────────────┘
                         │ calls
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌────────────────┐ ┌─────────────┐ ┌──────────────────┐
│ INTEGRITY      │ │ CONTEXT     │ │ NARRATIVE        │
│ AGENT          │ │ EXTRACTION  │ │ AGENT            │
│                │ │ AGENT       │ │                  │
│ (challenge &   │ │             │ │ (executive       │
│  audit)        │ │ (discovery  │ │  communication)  │
│                │ │  & ingest)  │ │                  │
│ - Assumption   │ │             │ │ - Executive      │
│   audit        │ │ - CRM/doc   │ │   summary        │
│ - Evidence     │ │   ingest    │ │ - Stakeholder-   │
│   scoring      │ │ - Entity    │ │   specific       │
│ - Duplication  │ │   extraction│ │   output         │
│   detection    │ │ - Pain      │ │ - Slide-ready    │
│ - Confidence   │ │   point     │ │   content        │
│   scoring      │ │   clustering│ │ - Objection      │
│ - Exception    │ │ - Stake-    │ │   handling       │
│   handling     │ │   holder    │ │ - Value          │
│                │ │   intent    │ │   hypothesis     │
│ Reports to     │ │   modeling  │ │   framing        │
│ primary as     │ │             │ │                  │
│ structured     │ │ Reports     │ │ Reports to       │
│ challenge      │ │ extracted   │ │ primary as       │
│ report         │ │ entities    │ │ structured       │
│                │ │             │ │ narrative        │
└────────────────┘ └─────────────┘ └──────────────────┘
```

The user experiences **one coherent system**. The critical steps are challenged and strengthened by specialists behind the scenes.

---

## 2. Capability Stack (5 Layers)

```text
LAYER 5: LIFECYCLE
─────────────────────────────────────────
Pre-Sale Business Case Creation
Implementation Success Metric Setup
Post-Sale Realization Tracking
Expansion Opportunity Modeling
Renewal Value Quantification

LAYER 4: COMMUNICATION
─────────────────────────────────────────
Executive Narrative Writing
Stakeholder-Specific Summaries
Slide-Ready Output Generation
Concise Recommendation Framing
Objection Anticipation & Response

LAYER 3: INTEGRITY
─────────────────────────────────────────
Assumption Audit
Evidence Scoring
Duplication Detection
Confidence Scoring
Exception Handling
Bad Modeling Prevention

LAYER 2: ANALYTICAL
─────────────────────────────────────────
Value Driver Analysis
Baseline Modeling
Benchmark Selection
Formula Application
Sensitivity Analysis
Scenario Modeling

LAYER 1: FOUNDATION
─────────────────────────────────────────
Entity Extraction
Taxonomy Mapping
Metric Normalization
Terminology Resolution
Document Understanding
```

**Design principle**: Each layer depends on the layer below. A Layer 3 (Integrity) skill can inspect and challenge outputs from Layer 2 (Analytical). A Layer 4 (Communication) skill can only package what Layer 2 produces and Layer 3 validates.

---

## 3. Agent Skill Matrix

### 3.1 Foundation Skills (Layer 1)

#### Skill: Business Context Extraction
*   **Purpose:** Pull structured meaning from raw inputs.
*   **Outputs:** Structured context object.

#### Skill: Stakeholder Intent Modeling
*   **Purpose:** Infer what each stakeholder cares about.
*   **Outputs:** Stakeholder map.

#### Skill: Taxonomy Mapping
*   **Purpose:** Map raw extracted terms into the canonical Value Fabric taxonomy.
*   **Outputs:** Normalized entities with confidence scores.

#### Skill: Metric Normalization
*   **Purpose:** Convert raw metric expressions into canonical, comparable, unit-specified metric definitions.
*   **Outputs:** Normalized metric.

### 3.2 Analytical Skills (Layer 2)

#### Skill: Value Driver Identification
*   **Purpose:** Recognize where value lives in the customer's business.
*   **Outputs:** Value driver map.

#### Skill: Capability Value Mapping
*   **Purpose:** Connect product capabilities to identified value drivers.
*   **Outputs:** Capability-Value chains.

#### Skill: KPI Selection
*   **Purpose:** Select the right metrics to measure the value drivers.
*   **Outputs:** KPI registry.

#### Skill: Baseline Reconstruction
*   **Purpose:** Estimate the customer's current state.
*   **Outputs:** Baseline metrics.

#### Skill: Financial Impact Modeling
*   **Purpose:** Calculate the financial impact of the proposed solution.
*   **Outputs:** Financial model.

#### Skill: Scenario Analysis
*   **Purpose:** Model different outcomes based on varying assumptions.
*   **Outputs:** Scenario analyses.

### 3.3 Integrity Skills (Layer 3)

#### Skill: Assumption Registry Management
*   **Purpose:** Track and validate all assumptions used in the model.
*   **Outputs:** Assumption registry.

#### Skill: Integrity Review
*   **Purpose:** Audit the model for logic errors, double-counting, and defensibility.
*   **Outputs:** Integrity artifact.

#### Skill: Evidence Alignment
*   **Purpose:** Ensure all claims are backed by sufficient evidence.
*   **Outputs:** Evidence assessment.

### 3.4 Communication Skills (Layer 4)

#### Skill: Value Narrative Composition
*   **Purpose:** Write the overarching story of the business case.
*   **Outputs:** Value narrative.

#### Skill: Executive Summary
*   **Purpose:** Distill the narrative into a concise summary for decision-makers.
*   **Outputs:** Executive summary.

#### Skill: Stakeholder Tailoring
*   **Purpose:** Adapt the narrative for different audiences.
*   **Outputs:** Stakeholder versions.

### 3.5 Lifecycle Skills (Layer 5)

#### Skill: Value Realization Planning
*   **Purpose:** Define how the promised value will be tracked and measured post-sale.
*   **Outputs:** Realization plan.

#### Skill: Expansion Detection
*   **Purpose:** Identify opportunities for further value creation.
*   **Outputs:** Expansion opportunities.

---

## 4. Governance and Quality Gates

### Gate 1: Context Completeness
*   Stakeholder coverage: ≥1 DECIDER or INFLUENCER identified.
*   Pain point clarity: ≥3 distinct pain points with evidence.

### Gate 2: Value Chain Integrity
*   No skipped steps: Every chain: Capability → UseCase → OpChange → Outcome → Metric.
*   Evidence per driver: Every ValueDriver has ≥1 Metric OR ≥1 ProofPoint.

### Gate 3: Financial Model Validity
*   Baseline present: Every impacted metric has a baseline.
*   Sensitivity range: ±20% on all estimates.

### Gate 4: Evidence Strength
*   CRITICAL claims: Must have STRONG evidence.
*   Benchmark currency: ≤2 years old.

### Gate 5: Narrative Quality
*   Bridge visible: Use → Operation → Outcome → Financial shown.
*   Traceability: Every number references source.
