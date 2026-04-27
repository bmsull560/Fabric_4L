# Agent Bill of Materials (ABOM) Architecture Report

## Executive Summary

The GATE (Governance, Audit, Trust, and Evidence) framework introduces the Agent Bill of Materials (ABOM) as the foundational contract for agent identity, capabilities, and constraints. This report details the functionality, purpose, and governance profile of the 9 canonical agents that comprise the Value Fabric Layer 4 Agentic Workflow Engine.

These 9 agents are divided into three functional categories:
1. **Value Spine Agents** (Artifact Producers)
2. **Operational Agents** (Data & Sync)
3. **Orchestration Agents** (Coordination & User Interaction)

---

## 1. Value Spine Agents

The Value Spine agents are responsible for the sequential generation of the core intelligence artifacts that power the platform.

### 1.1 ContextExtractionAgent
**Purpose:** Extracts customer context—including profile data, stakeholder maps, pain points, and financial metrics—from ingested sources. It serves as the top of the funnel for the value spine, producing the `ContextArtifact`.
- **Privilege Tier:** `standard`
- **Allowed Tools:** 7 (Knowledge graph traversal, semantic search, input validation)
- **Budget Limit:** $3.00 per run
- **Key Invariants:** Maximum of 50 tool calls per run; requires a minimum of 3 pain points to pass the gate; limited to 20 extraction sources.

### 1.2 ValueModelAgent
**Purpose:** Builds value chains, generates hypotheses, executes formulas, and performs ROI calculations and whitespace analysis. It translates raw context into quantified financial models, producing the `ValueModelArtifact`.
- **Privilege Tier:** `standard`
- **Allowed Tools:** 12 (Formula evaluation, ROI calculation, benchmark comparison, sensitivity analysis)
- **Budget Limit:** $5.00 per run
- **Key Invariants:** Maximum of 80 tool calls per run; capped at 50 formula evaluations and 1,000 sensitivity iterations per run.

### 1.3 IntegrityAgent
**Purpose:** Validates value model claims, checks formula correctness, flags unsupported assertions, and enforces evidence thresholds. It acts as the automated auditor between modeling and narrative generation, producing the `IntegrityArtifact`.
- **Privilege Tier:** `elevated`
- **Allowed Tools:** 7 (Graph queries, formula evaluation, benchmark comparison)
- **Budget Limit:** $4.00 per run
- **Key Invariants:** Maximum of 60 tool calls per run; requires a 0.7 confidence threshold for validation passes; limited to 3 validation retries.

### 1.4 NarrativeAgent
**Purpose:** Generates executive summaries, proposals, and stakeholder-ready business case documents. It synthesizes the validated value models into compelling prose, producing the `NarrativeArtifact`.
- **Privilege Tier:** `standard`
- **Allowed Tools:** 12 (Section generation, chart creation, table formatting, document assembly)
- **Budget Limit:** $8.00 per run
- **Key Invariants:** Maximum of 100 tool calls per run; document exports require human approval; limited to 12 sections per narrative and a 5MB maximum document size.

### 1.5 CompetitiveIntelAgent
**Purpose:** Analyzes the competitive landscape, economic differentiators, and market positioning. It enriches the value spine with external market context, producing the `CompetitiveIntelArtifact`.
- **Privilege Tier:** `elevated`
- **Allowed Tools:** 9 (Competitive analysis, benchmark comparison, graph traversal)
- **Budget Limit:** $5.00 per run
- **Key Invariants:** Maximum of 40 tool calls per run; limited to analyzing 6 competitors per run and 10 external API calls.

---

## 2. Operational Agents

Operational agents handle continuous background processes, data synchronization, and event monitoring.

### 2.1 SignalDetectionAgent
**Purpose:** Monitors data streams for operational pain signals, buying intent, and trigger events. It orchestrates Layer 2 extraction and Layer 3 evidence matching to surface actionable insights.
- **Privilege Tier:** `standard`
- **Allowed Tools:** 6 (Graph queries, semantic search, path finding)
- **Budget Limit:** $2.00 per run
- **Key Invariants:** Maximum of 30 tool calls per run; limited to processing 10 signals per request and matching 5 pieces of evidence per signal.

### 2.2 CRMSyncAgent
**Purpose:** Manages bidirectional CRM synchronization, reading from and writing to platforms like Salesforce and HubSpot.
- **Privilege Tier:** `high_privilege`
- **Allowed Tools:** 10 (Prospect data retrieval, opportunity updates, interaction history, lead scoring)
- **Budget Limit:** $1.00 per run
- **Key Invariants:** Maximum of 25 tool calls per run; **all CRM write operations and exports require human approval**; limited to 10 CRM writes per run; strictly requires tenant scoping.

---

## 3. Orchestration Agents

Orchestration agents manage the flow of work, either by coordinating other agents or by interacting directly with the user.

### 3.1 ConversationAgent (ValuePilot)
**Purpose:** Serves as the user-facing copilot. It receives chat messages from the RightRail interface, interprets user intent, delegates tasks to spine agents, and streams responses back to the user.
- **Privilege Tier:** `standard`
- **Allowed Tools:** 18 (Broad read access across knowledge, calculation, and generation tools)
- **Budget Limit:** $2.00 per run
- **Key Invariants:** Maximum of 15 tool calls per run; document exports require human approval; limited to 4,096 response tokens and a delegation depth of 1.

### 3.2 OrchestrationController
**Purpose:** Handles workflow scheduling, task distribution, and failure recovery. It coordinates multi-agent pipelines such as the ROI calculator, whitespace analysis, and business case generation workflows.
- **Privilege Tier:** `elevated`
- **Allowed Tools:** 20 (Comprehensive access across all domains except CRM writes)
- **Budget Limit:** $15.00 per run
- **Key Invariants:** Maximum of 200 tool calls per run; notifications and document exports require human approval; limited to managing 5 parallel agents and a maximum workflow duration of 600 seconds.

---

## Governance and Security Posture

The ABOM manifests enforce a strict principle of least privilege across the agent ecosystem:

1. **Tiered Access:** Only the `CRMSyncAgent` operates at the `high_privilege` tier, subjecting it to the strictest OPA policy evaluations and mandatory human-in-the-loop approvals for state-mutating actions.
2. **Financial Guardrails:** Every agent has a hardcoded `budget_limit_usd` per run, preventing runaway LLM costs. The `OrchestrationController` has the highest budget ($15.00) due to its coordination role, while operational agents operate on micro-budgets ($1.00 - $2.00).
3. **Deterministic Constraints:** Custom invariants (e.g., `max_sections_per_narrative`, `max_formula_evaluations_per_run`) ensure that agents operate within predictable bounds, preventing infinite loops and resource exhaustion.
