# Fabric_4L User Experience Design Brief

## Working Title

**From Signals to Justified Value: A Fluent Enterprise Value Workflow**

## Purpose

Fabric_4L should feel less like a collection of separate modules and more like a guided execution system that helps a user move from raw account context to a defensible business case.

The core user experience goal is:

> A user should be able to discover a business opportunity, classify its value path, build a driver tree, attach evidence, model financial impact, generate a budget justification, and track realized value through one continuous workflow.

The current architecture already contains many of the right ingredients: Value Packs, Signals, Evidence, Driver Trees, Formulas, Scenario Modeling, Business Cases, and Ground Truth. The design challenge is to make these pieces feel connected, contextual, and action-oriented.

---

# UX Problem Statement

Fabric_4L risks feeling like a set of powerful but isolated tools:

```text
Signals page
Evidence page
Driver tree page
Calculator page
Business case page
Agent right rail
```

Each feature may work individually, but the user experience breaks down if the user has to manually understand how one artifact becomes the next.

The desired experience is a fluent value journey:

```text
We found this opportunity
→ here is the likely value path
→ here is the driver tree
→ here is the evidence
→ here is the financial model
→ here is the executive-ready business case
→ here is what to track next
```

---

# Strategic UX Principle

## Design for Handoffs, Not Screens

The most important UX pattern is the handoff between steps.

Every major object should have a clear next action:

- Signal → Convert to value opportunity
- Opportunity → Classify value path
- Value path → Select driver tree
- Driver tree → Attach evidence
- Evidence → Support assumptions
- Assumptions → Resolve formulas
- Formulas → Model scenarios
- Scenarios → Generate business case
- Business case → Track realization

A feature should not be considered complete just because its screen exists. It is complete only when the user can enter it from the previous workflow step and continue naturally to the next one.

---

# Core User Journey

## Canonical Fabric_4L Workflow

```text
1. Account Context
2. Signal Discovery
3. Value Path Classification
4. Driver Tree Selection
5. Lever and Assumption Mapping
6. Evidence Attachment
7. Formula Resolution
8. Scenario Modeling
9. Business Case Generation
10. Realization Tracking
```

## Journey Description

### 1. Account Context

The user starts with an account, company, prospect, or customer. Fabric_4L identifies the relevant industry, segment, personas, product fit, and active Value Pack.

The experience should answer:

- Who is this account?
- What value pack applies?
- What business context do we already know?
- What data sources are connected?
- What should the user do first?

### 2. Signal Discovery

The system surfaces signals from websites, documents, CRM data, discovery notes, transcripts, public sources, or uploaded materials.

Signals may represent:

- Pain
- Inefficiency
- Revenue opportunity
- Risk
- Compliance pressure
- Strategic initiative
- Buying trigger
- Process friction

The user should be able to inspect each signal and understand why it matters.

### 3. Value Path Classification

Each signal should be translated into one or more value paths:

- Revenue Uplift
- Cost Savings / Efficiency
- Risk Reduction
- Productivity Gain
- Retention / Churn Reduction
- Time-to-Value Acceleration
- Compliance / Governance
- Strategic Optionality

This is the key bridge between raw intelligence and financial modeling.

### 4. Driver Tree Selection

The active Value Pack recommends a driver tree based on industry, persona, product use case, and signal type.

Example:

```text
Signal: Manual support ticket triage is slowing response time
Value Path: Cost Savings + Customer Experience + Retention Risk Reduction
Driver Tree: Support Productivity
  → Ticket triage time reduction
  → First-response time improvement
  → Escalation reduction
  → SLA breach reduction
```

### 5. Lever and Assumption Mapping

The user sees the operational levers that drive the financial case.

Examples:

- Hours saved per employee
- Tickets deflected
- Sales cycle days reduced
- Win rate improvement
- Churn reduction
- Downtime avoided
- Manual review reduction
- Compliance incidents avoided

Each lever should clearly connect to measurable assumptions.

### 6. Evidence Attachment

Evidence supports the assumptions and makes the business case credible.

Evidence may include:

- Internal customer data
- Benchmarks
- Case studies
- Public company signals
- CRM fields
- Product usage data
- Analyst research
- Discovery call excerpts
- Value Pack benchmarks

The user should see which assumptions are strongly supported, weakly supported, or unsupported.

### 7. Formula Resolution

The system maps assumptions to formulas from the relevant Value Pack.

Examples:

```text
Cost Savings = Hours Saved × Fully Loaded Cost × Adoption Rate
Revenue Uplift = Pipeline Impact × Conversion Lift × Average Contract Value
Risk Reduction = Loss Exposure × Probability Reduction × Impact Reduction
```

The user should understand how the math is derived and where each input comes from.

### 8. Scenario Modeling

The user models conservative, expected, and optimistic scenarios.

The scenario experience should allow the user to adjust assumptions while preserving traceability back to signals, evidence, formulas, and value paths.

### 9. Business Case Generation

The system generates an executive-ready business case that includes:

- Business problem
- Recommended initiative
- Value paths
- Financial impact
- ROI / payback
- Evidence
- Key assumptions
- Risks and sensitivities
- Stakeholder narrative
- Implementation or realization plan

The business case should not feel like generated marketing copy. It should feel like a traceable financial argument.

### 10. Realization Tracking

After the business case is approved or implemented, the system tracks whether the promised value happened.

This closes the loop between pre-sale promise and post-sale proof.

---

# UX Model: Multi-Path Value Justification

Fabric_4L should not force every business case into a cybersecurity-style avoided-loss model. Cyber tools often justify budget through risk reduction. Fabric_4L should support a broader enterprise value model.

## Primary Economic Value Paths

| Value Path | Core Question | Example |
|---|---|---|
| Revenue Uplift | How does this help the company make more money? | Higher win rate, expansion, faster sales cycles |
| Cost Savings | How does this help the company spend less? | Fewer manual hours, less rework, lower support costs |
| Risk Reduction | How does this reduce downside exposure? | Compliance risk, churn risk, outage risk, security risk |
| Productivity | How does this increase output per person? | More cases handled, faster analysis, fewer handoffs |
| Time-to-Value | How does this accelerate outcomes? | Faster onboarding, faster implementation, shorter cycle time |
| Strategic Value | How does this improve future capability? | Better governance, scalability, data foundation |

Most real enterprise value cases will be blended.

Example:

```text
A sales productivity platform may create:
- Cost savings through time saved
- Revenue uplift through more selling time
- Risk reduction through better forecast accuracy
```

---

# Role of Value Packs

Value Packs should act as workflow intelligence, not just static templates.

A Value Pack should help answer:

```text
Given this account, industry, persona, product, and signal:
  → What value path is likely?
  → Which driver tree applies?
  → Which formulas are appropriate?
  → Which benchmarks are credible?
  → Which evidence sources matter?
  → Which narrative should be generated?
```

## Example Value Pack Behaviors

### Manufacturing

Suggested value drivers may include:

- Downtime reduction
- Scrap reduction
- Throughput improvement
- Labor productivity
- Maintenance optimization
- Supply chain resilience
- Compliance risk reduction

### SaaS / AI / Data Platforms

Suggested value drivers may include:

- Sales cycle acceleration
- Expansion revenue
- Churn reduction
- Support deflection
- Engineering productivity
- Cloud cost optimization
- Data quality improvement

### Healthcare / MedTech

Suggested value drivers may include:

- Patient throughput
- Claims accuracy
- Clinical documentation time
- Compliance risk
- Staff productivity
- Readmission reduction

---

# Interaction Design Principles

## 1. Every Screen Needs a Primary Next Action

Each screen should make the next step obvious.

Examples:

- Signal detail: **Create Value Opportunity**
- Value opportunity: **Classify Value Path**
- Value path: **Build Driver Tree**
- Driver tree: **Attach Evidence**
- Evidence: **Use in Model**
- Scenario: **Generate Business Case**
- Business case: **Create Realization Plan**

## 2. Preserve Context Across the Journey

The app should always carry:

- tenantId
- accountId
- valuePackId
- signalId
- opportunityId
- valuePath
- driverTreeId
- modelId
- scenarioId
- businessCaseId

Losing context between screens breaks the workflow.

## 3. Make Handoffs Visible

Users should see how one artifact becomes another.

Example:

```text
This business case was generated from:
- 4 approved signals
- 2 value paths
- 1 driver tree
- 7 evidence items
- 5 financial assumptions
- 3 scenarios
```

## 4. Treat Evidence as a First-Class UX Element

Evidence should not be hidden in the background. It should be visible next to the assumptions it supports.

Each assumption should have an evidence status:

- Strongly supported
- Partially supported
- Unsupported
- User-provided
- Benchmark-derived
- Needs validation

## 5. Let the Agent Act in Context

The right rail agent should understand the current workflow context.

If the user is on a signal, the agent should know the signal.
If the user is on a driver tree, the agent should know the drivers and levers.
If the user is on a business case, the agent should know the assumptions, evidence, and scenario results.

Agent actions should mutate real app state where appropriate, not merely generate text.

Examples:

- “Find evidence for this assumption.”
- “Classify this signal into a value path.”
- “Suggest a driver tree.”
- “Create a conservative scenario.”
- “Rewrite this business case for the CFO.”

## 6. Design for Resume and Auditability

A user should be able to leave and return without losing progress.

The system should preserve:

- Current workflow step
- Selected value path
- Approved/rejected evidence
- Driver tree edits
- Scenario assumptions
- Generated business case versions
- Agent actions
- Audit trail

---

# Information Architecture Recommendation

## Top-Level Domains

The current Fabric_4L navigation structure (as implemented in LeftNavigation.tsx):

```text
Home
Accounts
Intelligence
Hypothesis
Driver Tree
Calculator
Value Case
Value Realization
```

## Account-Scoped Workflow

Inside an account, the user navigates through functional workspaces with their respective tabs:

**Intelligence Workspace** (/intelligence/:accountId):
- Signals
- Stakeholders
- Ontology Match
- Account Enrichment

**Hypothesis Workspace** (/hypothesis/:accountId):
- Hypothesis
- Discovery Questions
- Persona Fit
- Assumptions

**Driver Tree Workspace** (/drivers/:accountId):
- Driver Tree visualization and editing

**Calculator Workspace** (/calculator/:accountId):
- ROI
- Value Model

**Value Case Workspace** (/value-case/:accountId):
- Executive Value Case generation

**Value Realization Workspace** (/realization/:accountId):
- Realization Plan tracking

## Suggested Tabs

### Intelligence

- Signals
- Stakeholders
- Evidence Candidates
- Enrichment
- Ontology Match

### Value Studio

- Opportunities
- Value Paths
- Driver Tree
- Assumptions
- Scenarios
- Narrative

### Deliverables

- Business Cases
- Executive Briefs
- ROI Summaries
- Value Realization Plans

---

# Component Experience Pattern

## Recommended Page Layout

Each workflow screen should use a consistent layout:

```text
Page Header
  → account context
  → workflow status
  → primary action

Main Panel
  → current artifact
  → editable model/details

Right Rail
  → evidence
  → agent guidance
  → next action
  → audit trail

Footer or Sticky Action Bar
  → save
  → approve
  → continue
```

## Right Rail Modes

The right rail should support:

1. Detail panel
2. Evidence panel
3. Agent stream
4. Workflow history
5. Validation warnings

---

# Critical UX Questions for the Product Team

Use these as design review prompts:

1. Can a user tell what step they are on?
2. Can a user tell what artifact they are editing?
3. Can a user tell what data was used to create it?
4. Can a user tell what the next action is?
5. Can a user move forward without manually reconnecting context?
6. Can a user go back and revise a prior assumption?
7. Can a user see which evidence supports which number?
8. Can a user trust the generated business case?
9. Can a user resume the workflow later?
10. Can an admin or auditor trace how the final number was produced?

---

# Design Success Criteria

Fabric_4L succeeds when the user can say:

> “I understand where this value case came from, what evidence supports it, how the financial model works, and what I need to do next.”

The product should feel like:

```text
A guided value justification workspace
```

Not:

```text
A dashboard full of disconnected AI outputs
```

---

# Definition of Done for the UX Workflow

A workflow is UX-complete only when:

- The user can start from an account.
- Signals are discoverable and explainable.
- Signals can become value opportunities.
- Opportunities are classified into value paths.
- Value Packs recommend driver trees, formulas, benchmarks, and narratives.
- Driver trees feed assumptions.
- Evidence attaches to assumptions and drivers.
- Formulas produce financial outputs.
- Scenarios compare conservative, expected, and optimistic cases.
- Business cases trace back to the underlying signals, evidence, assumptions, and formulas.
- Agent actions operate in the current workflow context.
- The user can leave, return, and resume.
- The final output is executive-ready and auditable.

---

# Short Positioning Statement

Fabric_4L is a guided value justification platform that turns account intelligence into evidence-backed business cases.

It connects signals, value paths, driver trees, evidence, formulas, scenarios, and narratives into one fluent workflow so enterprise teams can quantify, defend, and track business value across revenue uplift, cost savings, and risk reduction.

