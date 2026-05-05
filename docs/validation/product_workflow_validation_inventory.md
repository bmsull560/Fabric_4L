# Product Workflow Validation Inventory

**Owner:** Product Engineering  
**Source:** User-provided comprehensive workflow validation inventory, integrated May 5, 2026.  
**Purpose:** This document is the product-level validation backlog for Fabric_4L. Frontend, backend, security, data, and operations validation matrices should map each release-significant workflow here to executable evidence before release-candidate sign-off.

## How to Use This Inventory

This inventory is intentionally broader than the frontend workflow coverage matrix. It captures the full product workflow surface, including authentication, tenant governance, ingestion, extraction, graph context, value-pack governance, calculation correctness, proposal generation, CRM integration, collaboration, search, notifications, administration, resilience, observability, and adversarial testing. The frontend matrix at `apps/web/docs/frontend-workflow-coverage-matrix.md` maps browser-test ownership for the most release-significant slices, while backend and platform suites should own API, persistence, queueing, model-governance, audit, and infrastructure-specific proof.

Below is a comprehensive Fabric_4L user workflow validation inventory. I would treat this as the master set of workflows that QA, product, security, and agent-validation should exercise before declaring the platform production-ready.

Fabric_4L Comprehensive User Workflow Validation List
1. Authentication, Tenant, and Workspace Access
 User signs up or is provisioned into a tenant.
 User logs in with email/password or SSO.
 User logs out successfully.
 User resets password.
 User enables or verifies MFA.
 User switches between workspaces or tenants, if permitted.
 User attempts to access a tenant they do not belong to.
 User with read-only role attempts a write action.
 User with admin role manages workspace settings.
 User session expires and re-authentication is required.
 User opens a deep link while unauthenticated and is redirected correctly.
 User opens a deep link without permission and receives a safe authorization error.
2. Account and Prospect Setup
 User creates a new prospect account.
 User imports an account from CRM.
 User manually enters account details.
 User enriches an account using company website/domain.
 User assigns an industry or value pack to the account.
 User overrides tenant default value pack for a specific account.
 User edits account metadata.
 User deletes or archives an account.
 User views account summary.
 User sees account-level readiness/completeness score.
 User handles duplicate account detection.
 User merges duplicate accounts.
 User views audit history for account changes.
3. Data Ingestion Workflows — Layer 1
 User uploads a document.
 User uploads multiple documents.
 User uploads unsupported file types.
 User uploads very large files.
 User uploads duplicate files.
 User imports content from a website.
 User imports CRM records.
 User imports call transcripts.
 User imports sales notes.
 User imports customer emails or meeting summaries.
 User connects an external data source.
 User disconnects an external data source.
 User views ingestion status.
 User retries a failed ingestion.
 User cancels an in-progress ingestion.
 User sees partial ingestion warnings.
 User sees provenance for every ingested item.
 User verifies source metadata, timestamps, and ownership.
 User confirms tenant isolation on ingested content.
4. Extraction and Signal Detection — Layer 2
 User runs extraction on uploaded content.
 User runs extraction on website content.
 User runs extraction on CRM opportunity data.
 User extracts pains, initiatives, metrics, stakeholders, risks, and desired outcomes.
 User reviews AI-extracted signals.
 User approves a signal.
 User rejects a signal.
 User edits a signal.
 User merges duplicate signals.
 User marks a signal as low-confidence.
 User filters signals by source, confidence, stakeholder, value category, or value pack.
 User views supporting evidence for a signal.
 User opens source citation from a signal.
 User validates signal-to-evidence grounding.
 User reruns extraction after adding new documents.
 User compares extraction results before and after new evidence.
 User handles conflicting evidence.
 User handles unsupported or noisy documents.
 User confirms PII detection and redaction behavior, where applicable.
5. Knowledge Graph and Context Engine — Layer 3
 User views generated account knowledge graph.
 User searches entities across the account context.
 User opens an entity detail view.
 User explores relationships between account, stakeholders, pains, initiatives, competitors, solutions, evidence, and value drivers.
 User views graph subgraph for a selected entity.
 User filters graph by entity type.
 User filters graph by evidence strength.
 User filters graph by source.
 User validates entity deduplication.
 User corrects an incorrectly merged entity.
 User creates a missing entity manually.
 User updates relationship labels.
 User verifies tenant-scoped graph isolation.
 User sees provenance on graph nodes and edges.
 User runs graph query from UI.
 User receives safe error for malformed graph query.
 User verifies graph refresh after new extraction.
6. Value Pack Selection and Governance
 User views available value packs.
 User selects a tenant default value pack.
 User assigns a value pack to an account.
 User composes multiple packs, such as SaaS + Healthcare.
 User views pack formulas.
 User views pack benchmarks.
 User views pack personas.
 User views pack ontology terms.
 User views pack-specific evidence requirements.
 User validates pack-driven signal classification.
 User validates pack-driven opportunity generation.
 User validates pack-driven formula recommendations.
 User tests account override against tenant default.
 User tests unsupported industry fallback behavior.
 Admin publishes a new value pack version.
 Admin deprecates an old value pack version.
 User sees warning when using deprecated pack logic.
 User confirms historical value cases preserve the original pack version.
7. Prospect Intelligence Workflow
 User opens /intelligence/:accountId/signals.
 User reviews pain signals.
 User reviews business initiatives.
 User reviews stakeholder map.
 User reviews ontology match.
 User reviews enrichment results.
 User filters intelligence by source and confidence.
 User opens right-rail detail panel for a signal.
 User asks the agent to explain a signal.
 User asks the agent for discovery questions.
 User asks the agent to find supporting evidence.
 User promotes a signal into a value hypothesis.
 User rejects irrelevant intelligence.
 User sees intelligence refresh after new sources are added.
 User exports prospect intelligence summary.
8. Stakeholder Mapping
 User views detected stakeholders.
 User adds a stakeholder manually.
 User edits stakeholder title, department, influence, and buying role.
 User links stakeholder to pains.
 User links stakeholder to initiatives.
 User links stakeholder to value drivers.
 User identifies economic buyer.
 User identifies technical buyer.
 User identifies champion.
 User identifies blocker.
 User asks agent for stakeholder-specific messaging.
 User generates discovery questions by stakeholder.
 User validates stakeholder evidence sources.
 User deletes or archives a stakeholder.
9. Hypothesis Generation Workflow — Layer 4
 User generates AI value hypotheses.
 User reviews multiple hypotheses.
 User approves a hypothesis.
 User modifies a hypothesis.
 User skips a hypothesis.
 User asks the agent to justify a hypothesis.
 User asks the agent to identify assumptions.
 User asks the agent to identify missing evidence.
 User maps hypothesis to stakeholder.
 User maps hypothesis to value category: revenue uplift, cost savings, or risk reduction.
 User converts approved hypothesis into value driver.
 User rejects hallucinated or unsupported hypothesis.
 User verifies every hypothesis has source grounding or a clear assumption label.
10. Value Driver Tree Workflow
 User opens value driver tree.
 User views AI-generated drivers.
 User views levers under each driver.
 User adds a custom driver.
 User edits driver title and description.
 User deletes a driver.
 User adds a lever.
 User maps lever to evidence.
 User maps lever to formula.
 User maps lever to stakeholder.
 User maps lever to business initiative.
 User changes driver priority.
 User filters drivers by EVF category.
 User validates driver-to-signal lineage.
 User validates driver-to-evidence lineage.
 User asks agent to suggest missing drivers.
 User asks agent to challenge weak drivers.
 User exports value driver tree.
11. Evidence Matching Workflow
 User opens evidence library.
 User views evidence items extracted from sources.
 User manually adds evidence.
 User links evidence to value levers.
 User unlinks incorrect evidence.
 User ranks evidence strength.
 User marks evidence as customer-provided.
 User marks evidence as benchmark-derived.
 User marks evidence as vendor-provided.
 User flags unsupported evidence.
 User opens source citation.
 User validates source quote or snippet.
 User handles conflicting evidence.
 User asks agent for stronger evidence.
 User filters evidence by source type.
 User filters evidence by confidence.
 User validates evidence provenance chain.
12. Benchmark and Ground Truth Workflow — Layers 5 and 6
 User views available benchmarks.
 User applies benchmark to a value model.
 User compares customer-specific metric against benchmark.
 User sees confidence level for benchmark.
 User sees benchmark source and date.
 User flags benchmark as inappropriate.
 User overrides benchmark with customer-provided data.
 User creates a ground-truth validation object.
 User approves validated assumptions.
 User rejects invalid assumptions.
 User records source of truth for a metric.
 User tracks validation status by metric.
 User sees warnings for stale benchmarks.
 Admin uploads new benchmark dataset.
 Admin applies benchmark governance policy.
 User validates benchmark policy enforcement.
13. Formula Selection and Calculation Workflow
 User views recommended formulas.
 User selects formula for a value lever.
 User edits formula inputs.
 User uses customer-specific values.
 User uses benchmark-derived values.
 User sees assumptions clearly labeled.
 User sees formula explanation.
 User sees calculation lineage.
 User runs calculation.
 User receives validation errors for missing inputs.
 User handles invalid numeric inputs.
 User compares multiple formula options.
 User locks approved assumptions.
 User unlocks and edits assumptions.
 User validates unit consistency.
 User validates currency handling.
 User validates time-period handling.
 User validates scenario-specific assumptions.
14. Value Calculator Workflow
 User opens value calculator.
 User views Conservative, Expected, and Optimistic scenarios.
 User edits scenario assumptions.
 User adds a new custom scenario.
 User duplicates a scenario.
 User deletes a scenario.
 User compares scenarios.
 User sees revenue uplift calculation.
 User sees cost savings calculation.
 User sees risk reduction calculation.
 User sees total economic value.
 User sees ROI.
 User sees payback period.
 User sees NPV, IRR, or other advanced metrics where enabled.
 User sees sensitivity analysis.
 User sees assumption confidence score.
 User sees missing-data warnings.
 User exports calculator output.
 User validates calculation reproducibility.
15. Business Case Generation Workflow
 User generates a business case.
 User selects business case template.
 User selects audience: CFO, CIO, CRO, COO, technical buyer, or executive sponsor.
 User includes or excludes selected drivers.
 User includes selected evidence.
 User includes selected benchmarks.
 User includes scenario comparison.
 User generates executive summary.
 User generates financial model narrative.
 User generates stakeholder-specific narrative.
 User edits generated business case.
 User asks agent to tighten argument.
 User asks agent to identify weak claims.
 User asks agent to add citations.
 User validates every claim maps to evidence, benchmark, or assumption.
 User exports business case to PDF, DOCX, or slides.
 User regenerates business case after model changes.
 User compares old and new versions.
16. Narrative and Proposal Workflow
 User generates value narrative.
 User generates proposal section.
 User generates discovery recap.
 User generates executive email.
 User generates mutual action plan.
 User generates renewal narrative.
 User generates expansion narrative.
 User adjusts tone and audience.
 User converts technical value into executive value.
 User verifies claims are grounded.
 User removes unsupported claims.
 User exports narrative content.
 User saves narrative version.
 User restores previous narrative version.
17. Agentic Chat and Right-Rail Workflow
 User opens agent panel.
 User asks a question about account intelligence.
 User asks for explanation of a value driver.
 User asks for evidence behind a claim.
 User asks for calculation explanation.
 User asks for missing assumptions.
 User asks for discovery questions.
 User asks for stakeholder messaging.
 User asks for risk analysis.
 User asks for next best action.
 Agent cites sources.
 Agent distinguishes fact, inference, benchmark, and assumption.
 Agent refuses or safely handles unsupported requests.
 User accepts an agent recommendation.
 User rejects an agent recommendation.
 User applies an agent-generated edit to the model.
 User resumes an interrupted agent workflow.
 User views agent reasoning summary without exposing unsafe internals.
 User sees agent execution status and errors.
18. Review, Approval, and Governance Workflow
 User submits value model for review.
 Reviewer approves value model.
 Reviewer requests changes.
 Reviewer comments on assumptions.
 Reviewer comments on evidence.
 Reviewer comments on calculations.
 Reviewer approves business case.
 Reviewer rejects unsupported business case.
 User resolves review comments.
 User resubmits for approval.
 System records approval history.
 System prevents export or publishing before required gates pass.
 Admin configures approval policy.
 Admin configures evidence threshold policy.
 Admin configures benchmark policy.
 Admin configures formula policy.
19. Versioning, Audit, and Traceability
 User views version history of account intelligence.
 User views version history of value model.
 User views version history of business case.
 User compares two versions.
 User restores previous version.
 User sees who changed what and when.
 User sees why a calculation changed.
 User sees source lineage from final claim back to raw source.
 User sees agent action audit trail.
 User sees approval audit trail.
 User exports audit report.
 User validates immutable records where required.
20. Collaboration Workflow
 User invites teammate.
 User assigns account owner.
 User assigns reviewer.
 User comments on signal.
 User comments on evidence.
 User comments on value driver.
 User mentions teammate.
 User resolves comment.
 User receives notification.
 User shares read-only link.
 User restricts access to confidential account.
 User sees real-time or refresh-based updates.
 User handles edit conflicts.
21. CRM and External System Workflow
 User connects CRM.
 User imports account.
 User imports opportunity.
 User imports contacts.
 User imports notes.
 User pushes value summary back to CRM.
 User pushes ROI fields back to CRM.
 User pushes business case link back to CRM.
 User handles CRM permission failure.
 User handles field mapping failure.
 User retries failed sync.
 User views sync log.
 Admin configures CRM field mapping.
 Admin disables CRM integration.
22. Value Realization Workflow
 User converts pre-sale value case into post-sale value realization plan.
 User defines target outcomes.
 User defines baseline metrics.
 User defines measurement cadence.
 User assigns metric owner.
 User records actual results.
 User compares projected vs realized value.
 User identifies variance.
 User generates value realization report.
 User generates renewal proof narrative.
 User generates expansion opportunity recommendation.
 User flags unrealized value risk.
 User creates follow-up action plan.
23. Search and Retrieval Workflow
 User searches accounts.
 User searches documents.
 User searches evidence.
 User searches stakeholders.
 User searches value models.
 User searches prior business cases.
 User searches across tenant knowledge.
 User filters search by account.
 User filters search by source type.
 User filters search by date.
 User opens result and lands in correct context.
 User validates search respects tenant boundaries.
 User validates search respects role permissions.
24. Notifications and Task Workflow
 User receives ingestion complete notification.
 User receives extraction complete notification.
 User receives review request notification.
 User receives approval notification.
 User receives failed sync notification.
 User receives stale benchmark notification.
 User receives missing evidence notification.
 User creates task.
 User assigns task.
 User completes task.
 User sees overdue task.
 User filters tasks by account or workflow stage.
25. Admin Configuration Workflow
 Admin manages users.
 Admin manages roles.
 Admin manages tenant settings.
 Admin manages value packs.
 Admin manages integrations.
 Admin manages data retention policy.
 Admin manages audit export settings.
 Admin manages approval gates.
 Admin manages benchmark policies.
 Admin manages formula policies.
 Admin manages branding.
 Admin views platform usage.
 Admin views failed jobs.
 Admin views security events.
 Admin views tenant health.
26. Security and Compliance User Workflows
 User attempts unauthorized tenant access.
 User attempts unauthorized account access.
 User attempts unauthorized document access.
 User attempts unauthorized export.
 User attempts prompt injection through uploaded document.
 User uploads content containing PII.
 User requests agent to reveal restricted data.
 User requests agent to ignore governance policy.
 User attempts cross-tenant search leakage.
 User validates role-based export restrictions.
 Admin exports audit log.
 Admin configures retention policy.
 Admin deletes account data according to policy.
 Admin validates deletion or archival behavior.
27. Error, Empty State, and Recovery Workflows
 User opens account with no data.
 User opens intelligence page before ingestion is complete.
 User opens calculator before formulas are configured.
 User opens business case before required evidence exists.
 User sees graceful error when L1 ingestion is unavailable.
 User sees graceful error when L2 extraction fails.
 User sees graceful error when L3 graph query fails.
 User sees graceful error when L4 agent execution fails.
 User sees graceful error when benchmark service is unavailable.
 User retries failed operation.
 User resumes partially completed workflow.
 User is prevented from losing unsaved work.
 User receives clear guidance on what to do next.
28. Full End-to-End Golden Path
 User creates new account.
 User assigns value pack.
 User ingests company website.
 User uploads discovery notes.
 System extracts signals.
 User approves signals.
 System builds account graph.
 User reviews stakeholder map.
 System generates value hypotheses.
 User approves hypotheses.
 System generates value driver tree.
 User maps evidence to drivers.
 User selects formulas.
 User fills assumptions.
 User creates Conservative, Expected, and Optimistic scenarios.
 System calculates ROI and payback.
 User generates business case.
 Reviewer approves business case.
 User exports business case.
 User pushes summary to CRM.
 User converts case into post-sale value realization plan.
29. Full End-to-End Adversarial Path
 User uploads noisy, contradictory, and partially irrelevant documents.
 User uploads document with prompt injection.
 System isolates instructions inside source content from system behavior.
 System extracts only grounded signals.
 User receives low-confidence warnings.
 Agent refuses unsupported claims.
 Calculator blocks invalid assumptions.
 Business case generation excludes unsupported claims.
 Review gate catches weak evidence.
 Audit trail records all decisions.
 No cross-tenant data appears in search, graph, agent, export, or logs.
30. Persona-Based Validation Journeys
Sales Rep
 Creates account.
 Imports discovery notes.
 Reviews signals.
 Generates value hypotheses.
 Builds first-pass business case.
 Generates executive email.
 Pushes summary to CRM.
Value Engineer
 Reviews evidence.
 Refines value drivers.
 Selects formulas.
 Validates assumptions.
 Builds scenarios.
 Produces CFO-ready business case.
Sales Leader
 Reviews pipeline value cases.
 Compares account-level ROI models.
 Identifies weak business cases.
 Reviews forecasted value impact.
 Approves strategic account cases.
Customer Success Manager
 Converts pre-sale case to realization plan.
 Tracks outcomes.
 Records actual results.
 Generates renewal narrative.
 Identifies expansion opportunity.
Admin
 Configures tenant.
 Manages users and roles.
 Configures value packs.
 Configures integrations.
 Reviews audit/security events.
 Manages governance policies.
Executive Buyer View
 Opens shared business case.
 Reviews executive summary.
 Reviews financial impact.
 Reviews assumptions.
 Reviews evidence.
 Reviews implementation risks.
 Downloads or shares final case.
Recommended Validation Grouping

For execution, I would group these into six validation suites:

Suite	Purpose
Golden Path E2E	Confirms the core account-to-business-case workflow works
Layer-by-Layer Validation	Validates L1 through L6 independently and together
Security/Tenant Isolation	Proves no cross-tenant leakage or unauthorized access
Agent Grounding and Governance	Confirms agents cite, constrain, explain, and refuse appropriately
Calculation and Evidence Integrity	Confirms formulas, assumptions, benchmarks, and evidence are traceable
Operational Resilience	Confirms failures, retries, partial states, and recovery paths work

The most important production-readiness workflows are:

 Account setup → ingestion → extraction → graph → hypotheses → value tree → calculator → business case.
 Evidence-to-claim traceability from final output back to raw source.
 Tenant isolation across every layer.
 Agent refusal and grounding under adversarial input.
 Formula correctness and scenario reproducibility.
 Review/approval gates before export or CRM push.
 Recovery from failed jobs and partial workflows.