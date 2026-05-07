# Fabric_LM MVP Feature Brief: Low-Effort Company Knowledge Onboarding

## Feature Name

**Company Knowledge Onboarding**

## One-Line Summary

When a new user signs up for Fabric_LM, the system should rapidly learn who they are, what their company sells, who they sell to, and how they create value using the least possible manual effort from the user.

## Product Thesis

Fabric_LM becomes more accurate and valuable when it has a structured understanding of the customer’s company, products, target buyers, value propositions, proof points, and ideal customer profile. The MVP should make this knowledge acquisition feel almost effortless: the user provides a website, optionally uploads or pastes an ICP, and the system generates a reviewable company knowledge profile that powers downstream value modeling, AI recommendations, discovery, ROI narratives, and business case generation.

The system should not ask users to manually fill out long onboarding forms. Instead, it should extract, infer, normalize, and ask only for targeted validation where confidence is low.

---

# 1. Problem

Fabric_LM needs context to generate accurate, useful, and defensible outputs.

Without company knowledge, the system will struggle to answer:

- What does this company sell?
- Who are the primary target customers?
- Which personas care about the product?
- What pain points does the product solve?
- What business outcomes does the product influence?
- Which value drivers are revenue, cost, or risk related?
- What proof exists?
- Which claims are supported versus inferred?
- How should ROI models be framed?

Today, most systems solve this by asking the user to fill out forms or upload large quantities of documentation. That creates friction and delays time-to-value.

Fabric_LM should instead use a **progressive knowledge acquisition model**: start with the website, enrich with ICP and sales materials, then continuously refine through user interactions and evidence.

---

# 2. MVP Goal

The MVP goal is to create a **Company Knowledge Profile** from minimal user input.

The user should be able to sign up, provide a company website and optional ICP, and receive a structured, reviewable knowledge profile within the onboarding experience.

The profile should become the foundation for:

- Product understanding
- Persona mapping
- ICP alignment
- Use case extraction
- Value driver mapping
- ROI model generation
- Discovery question generation
- Proof/evidence matching
- Sales narrative generation
- Business case creation

---

# 3. Target Users

## Primary User

**Value engineer, sales leader, founder, or product marketer** who wants Fabric_LM to generate better business value models with minimal setup effort.

## Secondary Users

- Customer success leaders
- Enablement leaders
- RevOps teams
- Solution consultants
- Product marketing teams
- AI/business case platform administrators

---

# 4. Core User Story

As a new Fabric_LM user, I want to give the system my company website and ICP so that it can automatically understand my company, products, target buyers, and value propositions without requiring me to manually configure everything.

---

# 5. MVP Inputs

## Required Input

### 1. Company Website

The website is the lowest-effort and highest-coverage starting point.

The user provides:

- Company website URL

The system extracts:

- Company description
- Product and platform pages
- Use case pages
- Industry pages
- Persona/role pages
- Case studies
- Pricing and packaging claims, if available
- Integrations
- Security/trust content
- Blog/resource themes, if useful

## Strongly Recommended Input

### 2. Ideal Customer Profile

The user can provide their ICP in one of three easy ways:

- Paste ICP text
- Upload a document
- Answer a lightweight guided ICP prompt

The system extracts:

- Target company size
- Target industries
- Buyer personas
- User personas
- Common pain points
- Trigger events
- Qualification criteria
- Disqualification criteria
- Competitive context
- Buying committee structure
- Typical sales motion

## Optional Inputs

### 3. Product/Marketing Assets

Examples:

- Pitch deck
- Product one-pager
- Case studies
- ROI calculator
- Value framework
- Sales playbook
- Battlecard
- Demo script
- Discovery guide

### 4. CRM or Sales Data Later

Not required for MVP, but future expansion could connect:

- Salesforce
- HubSpot
- Gong/Chorus
- Notion/Google Drive
- Enablement platforms
- Customer success systems

---

# 6. Lowest-Effort Knowledge Acquisition Strategy

## Principle

Do not ask the user to build the knowledge model. Ask for one or two high-leverage inputs and let the system produce a draft.

## MVP Flow

### Step 1: User Provides Website

Prompt:

> “Enter your company website so Fabric_LM can understand your products, buyers, use cases, and value drivers.”

User action:

- Enter URL

System action:

- Crawl high-signal pages
- Classify page types
- Extract structured value objects
- Create a provisional Company Knowledge Profile

### Step 2: User Provides ICP

Prompt:

> “Add your ICP so Fabric_LM can tailor value models to your best-fit customers.”

User options:

- Paste ICP
- Upload ICP
- Skip for now
- Generate ICP draft from website

System action:

- Parse ICP into structured criteria
- Compare ICP against website-derived positioning
- Identify gaps, conflicts, and assumptions

### Step 3: System Generates Draft Knowledge Profile

The system presents a reviewable summary:

- Company
- Products
- Target customers
- Buyer personas
- User personas
- Use cases
- Pain points
- Capabilities
- Value drivers
- Proof points
- Metrics
- ICP assumptions
- Confidence scores

### Step 4: User Reviews Only Exceptions

Instead of asking the user to review everything, the UI should highlight:

- Low-confidence items
- Conflicting claims
- Missing ICP fields
- Unsupported value claims
- Ambiguous personas
- Unclear product categories

This keeps the human effort focused where it matters.

### Step 5: System Stores Approved Knowledge

Once approved, the profile becomes the tenant’s active company knowledge layer.

The user can then use Fabric_LM to generate:

- Value models
- Discovery questions
- Persona-specific business cases
- ROI assumptions
- Value hypotheses
- Customer-specific narratives

---

# 7. Key MVP Feature: Company Knowledge Profile

## Description

The Company Knowledge Profile is the structured, reviewable representation of what Fabric_LM knows about the user’s company.

It should be generated automatically, editable by the user, and stored as governed tenant knowledge.

## Suggested Profile Sections

### 1. Company Identity

- Company name
- Website
- Category
- Short description
- Long description
- Market positioning
- Primary business model

### 2. Product Catalog

- Product names
- Platform/module structure
- Product descriptions
- Core capabilities
- Feature groups
- Product-to-capability relationships

### 3. Target Customer / ICP

- Target industries
- Company size
- Geography
- Maturity level
- Existing systems/tools
- Buying triggers
- Qualification criteria
- Disqualification criteria

### 4. Personas

- Economic buyer
- Technical buyer
- Champion
- End user
- Influencer
- Procurement/legal/security stakeholders

Each persona should include:

- Goals
- Pain points
- objections
- success metrics
- relevant value drivers

### 5. Use Cases

- Primary use cases
- Secondary use cases
- Industry-specific use cases
- Persona-specific use cases
- Capability dependencies

### 6. Value Drivers

Map all value claims to the Economic Value Framework:

- Revenue Uplift
- Cost Savings
- Risk Reduction

Each value driver should include:

- Source claim
- Normalized value category
- Metric candidates
- Relevant personas
- Supporting proof
- Confidence score

### 7. Proof & Evidence

- Case studies
- Customer quotes
- Quantified outcomes
- Logos
- Analyst references
- Security/compliance claims
- Integration proof

Each proof point should be linked to:

- Product
- Capability
- Use case
- Persona
- Value driver
- Source URL or document

### 8. Trust & Commercial Context

- Security certifications
- Compliance claims
- Pricing model
- Packaging
- Integrations
- Deployment model
- Implementation requirements

---

# 8. Where This Knowledge Should Be Stored

Fabric_LM should use a layered storage model rather than one flat database table.

## 1. Raw Source Store

Stores the original source material.

Includes:

- Raw HTML
- Cleaned page text
- Uploaded documents
- Parsed document text
- Source metadata
- Crawl timestamp
- Hash/version
- Tenant ID

Best storage:

- Object storage for raw files and snapshots
- Postgres metadata table for source records

Purpose:

- Auditability
- Reprocessing
- Provenance
- Traceability

## 2. Extraction Record Store

Stores structured outputs from each source before promotion to the knowledge graph.

Includes:

- Extracted products
- Capabilities
- Personas
- ICP criteria
- Use cases
- Value drivers
- Proof points
- Confidence scores
- Trace spans
- Source references
- Extraction version

Best storage:

- Postgres JSONB records with typed schemas

Purpose:

- Review queue
- Human validation
- Retry/reprocessing
- Version comparison

## 3. Company Knowledge Graph

Stores approved, normalized company knowledge.

Core graph entities:

- Company
- Product
- Capability
- UseCase
- Persona
- Industry
- ICP
- PainPoint
- ValueDriver
- Metric
- ProofPoint
- Integration
- TrustClaim
- CommercialModel

Core graph relationships:

- Company OFFERS Product
- Product ENABLES Capability
- Capability SUPPORTS UseCase
- UseCase BENEFITS Persona
- Persona HAS PainPoint
- UseCase DRIVES ValueDriver
- ValueDriver MEASURED_BY Metric
- ProofPoint VALIDATES Capability / UseCase / ValueDriver
- ICP TARGETS Industry / Persona / Segment
- TrustClaim SUPPORTS EnterpriseReadiness

Best storage:

- Neo4j or graph database

Purpose:

- Reasoning
- Relationship traversal
- Persona-specific narratives
- Value model generation
- Explainable AI outputs

## 4. Semantic Retrieval Index

Stores embeddings for retrieval and grounding.

Includes:

- Website page chunks
- Uploaded document chunks
- Case study chunks
- ICP chunks
- Product copy
- Proof/evidence snippets

Best storage:

- Vector database or Postgres pgvector

Purpose:

- RAG
- Source-backed answers
- Evidence lookup
- Prompt grounding

## 5. Tenant Configuration / Active Knowledge Profile

Stores the active version of the company profile used by the application.

Includes:

- Active profile ID
- Approved knowledge graph version
- Default ICP
- Preferred value framework
- Company-specific terminology
- Product taxonomy settings
- Review status

Best storage:

- Postgres relational tables

Purpose:

- Fast application access
- Tenant-level governance
- Version control
- Admin workflows

---

# 9. MVP Data Model

## CompanyKnowledgeProfile

```json
{
  "id": "ckp_123",
  "tenant_id": "tenant_123",
  "company_name": "ExampleCo",
  "website": "https://example.com",
  "status": "draft | needs_review | approved",
  "version": 1,
  "confidence_score": 0.82,
  "created_at": "2026-05-07T00:00:00Z",
  "updated_at": "2026-05-07T00:00:00Z"
}
```

## KnowledgeSource

```json
{
  "id": "src_123",
  "tenant_id": "tenant_123",
  "profile_id": "ckp_123",
  "source_type": "website | icp | upload | manual",
  "source_url": "https://example.com/products",
  "document_name": null,
  "content_hash": "abc123",
  "crawl_status": "complete",
  "authority_weight": "high | medium | low"
}
```

## ValueExtractionRecord

```json
{
  "id": "ver_123",
  "source_id": "src_123",
  "tenant_id": "tenant_123",
  "page_type": "product | use_case | case_study | pricing | trust | blog",
  "extracted": {
    "products": [],
    "capabilities": [],
    "personas": [],
    "industries": [],
    "use_cases": [],
    "value_drivers": [],
    "metrics": [],
    "proof_points": []
  },
  "confidence": 0.78,
  "requires_review": true
}
```

## ICPProfile

```json
{
  "id": "icp_123",
  "tenant_id": "tenant_123",
  "profile_id": "ckp_123",
  "industries": [],
  "company_size": [],
  "buyer_personas": [],
  "user_personas": [],
  "pain_points": [],
  "trigger_events": [],
  "qualification_criteria": [],
  "disqualification_criteria": [],
  "confidence": 0.86
}
```

---

# 10. MVP User Experience

## Onboarding Screen 1: Company URL

Title:

**Teach Fabric_LM about your company**

Prompt:

“Start with your website. Fabric_LM will scan your product, solution, case study, trust, and pricing pages to build a draft company knowledge profile.”

Fields:

- Company website URL
- Company name, auto-detected but editable

CTA:

**Analyze Website**

## Onboarding Screen 2: ICP

Title:

**Add your ideal customer profile**

Prompt:

“Your ICP helps Fabric_LM tailor value models to the customers you actually want to win.”

Options:

- Paste ICP
- Upload ICP document
- Generate draft ICP from website
- Skip and refine later

CTA:

**Add ICP** or **Generate Draft ICP**

## Onboarding Screen 3: Review Draft Profile

Title:

**Review what Fabric_LM learned**

Sections:

- Products
- Target customers
- Personas
- Use cases
- Value drivers
- Proof points
- Open questions

UX pattern:

- Show confidence score per section
- Allow accept/edit/reject
- Highlight only uncertain fields
- Provide “Looks good” bulk approval

CTA:

**Approve Company Profile**

## Onboarding Screen 4: First Value Output

Immediately show value:

- “Here are 5 value hypotheses Fabric_LM can now generate for your target customers.”

Example outputs:

- Target persona
- Pain point
- Value driver
- Metric candidate
- Suggested discovery question
- Supporting source

CTA:

**Create First Value Model**

---

# 11. MVP Knowledge Confidence Model

Each extracted object should have a confidence status.

## Confidence Levels

### High Confidence

Source is explicit and authoritative.

Examples:

- Product page states product capability
- Pricing page states commercial model
- Trust page states SOC 2 status
- Case study includes quantified outcome

### Medium Confidence

Source is explicit but general.

Examples:

- Homepage claim
- About page positioning
- Blog explanation of market problem

### Low Confidence

Source is inferred or weakly supported.

Examples:

- Persona inferred from language
- Value driver inferred from vague benefit
- Metric inferred from use case
- ICP criteria inferred from examples

## Governance Rule

Low-confidence knowledge can be used for draft hypotheses, but not for approved business cases without user validation or stronger evidence.

---

# 12. MVP Scope

## In Scope

- Company website URL ingestion
- Basic crawl of high-signal pages
- Page classification
- Text extraction and chunking
- ICP paste/upload
- Structured extraction into Company Knowledge Profile
- Review and approval UI
- Source provenance
- Confidence scoring
- Storage of raw source, extraction records, and approved profile
- Basic graph representation of company/product/persona/use case/value driver/proof relationships
- First generated value hypotheses

## Out of Scope for MVP

- Full CRM integration
- Continuous website monitoring
- Deep competitive intelligence
- Multi-language extraction
- Automated ROI calculator generation from every claim
- Complex workflow automation
- Human approval workflows with multiple roles
- Enterprise SSO and permissions beyond basic tenant isolation
- Full benchmark library integration
- Real-time sales call intelligence

---

# 13. Success Metrics

## Activation Metrics

- Percentage of new users who complete website scan
- Percentage who add or generate ICP
- Time from signup to first Company Knowledge Profile
- Time from signup to first value hypothesis

## Quality Metrics

- User approval rate of extracted products
- User approval rate of personas
- User approval rate of use cases
- User approval rate of value drivers
- Number of required manual edits
- Confidence improvement after review

## Business Metrics

- Signup-to-first-value-model conversion rate
- Trial activation rate
- Number of generated business cases
- Retention of users who complete onboarding versus those who do not

---

# 14. Key Design Decisions

## Decision 1: Website First

The website is the lowest-effort default input and should be the first onboarding step.

## Decision 2: ICP Second

ICP should be strongly recommended but not required. Users who do not have a formal ICP should be able to generate a draft from the website.

## Decision 3: Review Exceptions, Not Everything

The user should not be forced to validate every extracted field. The system should only ask for validation where confidence is low or contradictions exist.

## Decision 4: Store Raw, Extracted, and Approved Knowledge Separately

This prevents the system from confusing source material with approved truth.

## Decision 5: Knowledge Must Be Versioned

Company knowledge will evolve. Product pages change, ICP changes, pricing changes, and value messaging changes. Every profile should support versioning.

---

# 15. Recommended MVP Architecture

## Frontend

- React/Vite or Next.js
- Onboarding wizard
- Review/edit interface
- Confidence badges
- Source citation drawers
- Company profile dashboard

## Backend

- FastAPI
- Background crawl job
- Extraction worker
- Typed extraction schemas
- Tenant-aware storage
- Approval endpoint
- Profile generation endpoint

## Storage

- Object storage for raw website/doc snapshots
- Postgres for source metadata, extraction records, profile versions, and tenant configuration
- Neo4j for approved knowledge graph
- Vector index for retrieval and source grounding

## Core Services

1. Ingestion Service
2. Extraction Service
3. Normalization Service
4. Review/Profile Service
5. Knowledge Graph Service
6. Value Hypothesis Generator

---

# 16. First Release Acceptance Criteria

The MVP is ready when a user can:

- Create an account
- Enter a company website
- Trigger a website scan
- Add or generate an ICP
- Review extracted company knowledge
- Approve the Company Knowledge Profile
- See source-backed products, personas, use cases, and value drivers
- Generate at least five value hypotheses from the approved profile
- Trace every major claim back to a source or user-provided input

---

# 17. MVP Feature Summary

Fabric_LM should make onboarding feel like this:

1. “Give us your website.”
2. “Add your ICP if you have one.”
3. “We built your company knowledge profile.”
4. “Review the few things we are unsure about.”
5. “Now here are value hypotheses and ROI model starting points tailored to your company and target customer.”

This creates fast time-to-value while building the structured knowledge foundation required for accurate, explainable, and defensible AI-generated business value outputs.

