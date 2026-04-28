# Canonical User Journeys

This document defines the core end-to-end user journeys for the Value Fabric platform. These journeys form the foundation of our 4-layer testing strategy, ensuring that critical business workflows are validated across the UI, backend contracts, and performance boundaries.

## Journey 1: Domain Ingestion to Value Tree Exploration (The "Happy Path")
This is the primary onboarding and discovery workflow for a new prospect.

**Workflow Steps:**
1. User logs in and establishes tenant context.
2. User navigates to the Command Center (`/home`).
3. User submits a new company domain for ingestion.
4. User monitors the ingestion job until completion.
5. User navigates to the Value Tree Explorer (`/context/value-trees/explorer`).
6. User validates that the newly ingested domain has generated expected nodes (Capabilities, Use Cases, Personas, Value Drivers).
7. User verifies that node statistics and confidence badges are displayed correctly.

**Key Invariants:**
- The ingestion job must successfully trigger the L1 -> L2 -> L3 pipeline.
- The resulting graph data must be strictly scoped to the user's `tenant_id`.

## Journey 2: Intelligence Workspace Synthesis
This journey validates the core agentic workflow where raw data is synthesized into actionable intelligence.

**Workflow Steps:**
1. User navigates to the Accounts list (`/accounts`).
2. User selects an account, entering the Intelligence Workspace (`/intelligence/:accountId/signals`).
3. User triggers the Agent Stream to synthesize recent signals.
4. User interacts with the agent (e.g., asks a follow-up question).
5. User navigates through the Intelligence tabs (Drivers, Evidence, Stakeholders) to verify that the synthesized data populates the respective views.

**Key Invariants:**
- The agent workflow must successfully transition through idle -> running -> finished states.
- The generated intelligence must be persisted and retrievable across tabs.

## Journey 3: Value Studio Deliverable Generation
This journey validates the creation of a business case or narrative from synthesized intelligence.

**Workflow Steps:**
1. User navigates to the Value Studio for a specific account (`/studio/:accountId/action-plan`).
2. User reviews the action plan and proceeds to the Value Model tab.
3. User adjusts a variable or formula within the value model.
4. User navigates to the Narrative tab and generates a narrative based on the updated model.
5. User exports or views the final deliverable (e.g., CFO View at `/deliverables/views/cfo`).

**Key Invariants:**
- Formula evaluations must correctly recalculate based on variable changes.
- The generated narrative must reflect the updated value model data.

## Journey 4: Governance and Trust Validation
This journey ensures that the platform's trust layer correctly tracks and audits decisions.

**Workflow Steps:**
1. User navigates to the Governance Decision Traces (`/governance/traces`).
2. User selects a recent agent decision or synthesis output.
3. User verifies the provenance of the data (linking back to the original ingested source).
4. User navigates to the Audit Log (`/governance/audit/log`) to verify that their recent actions (e.g., domain ingestion, model update) are recorded.

**Key Invariants:**
- Every AI-generated output must have a traceable provenance path.
- Audit logs must accurately capture user actions with correct timestamps and tenant scoping.

## Journey 5: Tier-Gated Access and Security
This journey validates that the platform correctly enforces RBAC and tier-based feature gating.

**Workflow Steps:**
1. User logs in with a "Standard" tier account.
2. User verifies that advanced features (e.g., Context Engine, Governance) are hidden from the navigation.
3. User attempts to directly access a restricted URL (e.g., `/context/ontology`) and is redirected to `/home`.
4. User logs out and logs back in with an "Admin" tier account.
5. User verifies that all features and settings are accessible.

**Key Invariants:**
- Route guards must strictly enforce tier requirements.
- API requests to restricted endpoints must return 403/401 if bypassed at the UI layer.
