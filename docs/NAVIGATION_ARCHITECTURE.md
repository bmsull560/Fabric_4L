# Fabric 4L: Navigation Architecture Specification

## 1. Strategic Foundation

Fabric 4L is a **sales-oriented value selling platform**. It is not a generic analytics dashboard or a general-purpose consulting tool. The user is a sales engineer or value consultant at a vendor, and their goal is to prove that *their specific product* solves the prospect's validated problems.

The core cognitive spine of the product is **Progressive Synthesis**:
`Signal (Prospect Pain) → Explanation (Root Cause) → Proof (Evidence) → Audience Translation (Who Cares) → Intervention (Our Product Capability) → Quantified Value (The Business Case)`

To support this, the navigation architecture is strictly separated into three distinct layers:
1. **Global Product Navigation (Left Rail):** Durable location markers (Where am I?).
2. **Workspace Navigation (Horizontal Tabs):** The reasoning flow (What am I doing?).
3. **Contextual Support (Right Rail):** Dynamic assistance (What do I need right now?).

---

## 2. Global Product Navigation (Left Rail)

The left rail establishes the primary domains of the application. It resolves the tension between "Intelligence" (knowing the prospect) and "Value Studio" (arguing for our product) by explicitly separating them.

*   **Accounts:** The entry point for selecting a target company or prospect.
*   **Intelligence:** The discovery and validation workspace. This is where the system helps the user determine what is happening in the prospect's business, why it is happening, and whether the conclusion is credible.
*   **Value Studio:** The synthesis workspace. This is where validated prospect intelligence is mapped to the vendor's product capabilities to assemble a formal business case, narrative, and calculator.
*   **Context Engine:** The vendor's knowledge base. This is where the vendor's own Value Packs, product capabilities, ROI formulas, and case studies live.
*   **Deliverables:** The activation layer. A library of packaged outputs (PDFs, interactive links, slides) ready for sharing with the prospect.
*   **Governance:** The trust layer. Audit logs, decision traces, and compliance tracking.
*   **Settings:** Tenant configuration, integrations, and user management.

---

## 3. Workspace Navigation: Intelligence vs. Value Studio

The most critical architectural decision is the separation of the reasoning flow across two distinct workspaces. This prevents "Value Model" from feeling like a hollow sibling tab and instead positions it as the destination artifact.

### 3.1 The Intelligence Workspace (The "Knowing" Phase)
When a user selects an Account, they land in the Intelligence workspace by default. The tabs here represent the **Core Reasoning Stages** focused entirely on the *prospect*.

*   **Signals (Default Landing):** The entry point. Surfaces candidate pain points, opportunities, and anomalies detected in the prospect's data. *Goal: Prioritization of prospect pain.*
*   **Drivers:** The explanation layer. Connects signals to root causes (e.g., linking "production downtime" to "aging equipment"). *Goal: Causal understanding of the prospect's business.*
*   **Evidence:** The trust layer. Grounds signals and drivers in source material, extracted observations, and confidence framing. *Goal: Validation of the prospect's reality.*
*   **Stakeholders:** The translation layer. Maps validated findings to specific buyer personas within the prospect account and their unique concerns. *Goal: Organizational meaning for the prospect.*

### 3.2 The Value Studio Workspace (The "Arguing" Phase)
Once prospect intelligence is validated, the user moves to Value Studio to formalize the case. The tabs here represent the **Synthesis Stages** where the *prospect's pain* meets the *vendor's product*.

*   **Action Plan (The "Why Us" Argument):** The intervention layer. This is not a generic to-do list. It maps validated prospect pain signals to specific capabilities of the vendor's product, backed by the vendor's proof points (case studies, benchmarks). *Goal: Product-anchored intervention.*
*   **Value Model:** The quantification layer. The destination artifact where selected signals, drivers, and product capabilities are calculated into a financial business case. *Goal: Quantified value of the vendor's solution.*
*   **Narrative:** The storytelling layer. Packages the model into a cohesive, stakeholder-ready story tailored to the prospect's buying committee. *Goal: Persuasion.*

---

## 4. Contextual Support (Right Rail)

The right rail is a dynamic, contextual assistant that changes based on the active workspace tab. It does not introduce new navigation paths; it supports the current task. It operates in two primary modes:

**1. Detail Panel (Inspect Mode):**
*   Deep dive into the currently selected item (e.g., a specific Signal or Driver).
*   Evidence excerpts (direct quotes or snippets from source documents).
*   Confidence & Assumptions (transparency into the AI's reasoning).

**2. Agent Stream (Co-Pilot Mode):**
*   Proactive summaries of findings.
*   Structured next actions (e.g., "Generate value driver tree," "Draft action plan").
*   Conversational interface for co-creation.

**Persistent Element:**
*   **"Selected-for-Model" Tray:** A persistent cart showing which findings have been bookmarked for inclusion in the final Value Model.

---

## 5. Mapping to the Fabric_4L Codebase

This new architecture requires a refactor of the existing `TieredNav.tsx` and routing structure in `App.tsx`.

### Current State vs. Target State

| Current Fabric_4L Route | Target Architecture Mapping | Required Action |
| :--- | :--- | :--- |
| `/discover/accounts` | **Accounts** (Left Rail) | Maintain as primary entry point. |
| `/workflow/prospect` | **Intelligence -> Signals** | Integrate AI-surfaced signals; remove manual upload dependency. |
| `/model/value-studio/mapping` | **Intelligence -> Drivers** | Connect to Neo4j `(Pain)-[:SOLVED_BY]->(Capability)` graph. |
| `/model/value-studio/validation` | **Intelligence -> Evidence** | Integrate `IntegrityAgent` backend for source verification. |
| `/model/value-studio/narrative` | **Intelligence -> Stakeholders** | Refocus on persona mapping before narrative generation. |
| *(New)* | **Value Studio -> Action Plan** | Build product-anchored recommendations view. |
| `/model/value-studio/modeling` | **Value Studio -> Value Model** | Enhance with variable-driven recalculation. |
| `/deliver/cases` | **Deliverables** (Left Rail) | Consolidate output library. |

### Implementation Phasing

1.  **Phase 1: Navigation Skeleton Update:** Refactor `TieredNav.tsx` to reflect the new Global Left Rail (Accounts, Intelligence, Value Studio, Context Engine, Deliverables, Governance, Settings).
2.  **Phase 2: Workspace Routing:** Update `App.tsx` to route Account selections directly into the Intelligence workspace with the new tab structure.
3.  **Phase 3: Component Migration:** Migrate existing `Stage1` through `Stage6` components into their new homes under Intelligence and Value Studio, updating their internal logic to fit the "Progressive Synthesis" model.
4.  **Phase 4: Right Rail Implementation:** Build the global contextual right rail component with Detail and Agent Stream modes.
