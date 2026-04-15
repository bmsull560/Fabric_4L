# Frontend Screen Documentation

A comprehensive reference of all screens in the Value Fabric Platform, organized by navigation section and user tier.

---

## Tier Legend

- **[standard]** — Available to all business users
- **[advanced]** — Power-user tools (toggle-enabled for standard users)
- **[admin]** — Governance and configuration controls

---

# Home

## Home / Command Center **[standard]**

**1. Context**
The entry point for all users. Provides an overview of the platform's current state and quick access to common workflows.

**2. Objective**
Orient the user, surface actionable insights, and enable rapid navigation to frequently used features without cognitive overload.

**3. Mental Model**
A mission control dashboard where live workflows, recent activity, and system health coexist. Think "today's priorities + system pulse."

**4. Layout**
- **Hero Zone:** Welcome message + key metric summary (active workflows, pending cases)
- **Quick Actions Grid:** 4-6 primary action cards (Run Extraction, New Business Case, Browse Value Packs, View Accounts)
- **Activity Stream:** Recent workflows, notifications, and system events
- **Status Bar:** Health indicators and active job count

**5. Key Interactions**
- Click action cards to navigate or trigger workflows
- Hover activity items for context preview
- Click notification badges to expand details
- Refresh button for real-time status updates

**6. State Transitions**
- Empty state: Onboarding prompts when no workflows exist
- Loading state: Skeleton cards while data hydrates
- Error state: Retry options for failed data fetches
- Active state: Live SSE updates for running workflows

**7. Data + Agent Behavior**
- `useActiveWorkflows()` polls Layer 4 for running workflows
- `useWorkflowSSE()` streams real-time progress updates
- Agents surface pending approvals and failed jobs requiring attention
- Data: workflow status, business case summaries, recent traces

**8. Output / Next Step**
- Navigation to specific workflows or business cases
- Launch new extraction or analysis jobs
- Acknowledge notifications and dismiss badges

**9. Edge Cases**
- No workflows: Show sample data + quick-start templates
- All systems degraded: Display incident banner with status page link
- High notification volume: Collapse to "N unread" with expand option

---

# Library

## Value Packs **[standard]**

**1. Context**
Pre-built value models, formulas, and templates organized by industry vertical. The content marketplace of the platform.

**2. Objective**
Enable users to discover, preview, and activate pre-configured value models without building from scratch.

**3. Mental Model**
An app store for value models. Browse categories, read reviews (usage stats), install with one click.

**4. Layout**
- **Filter Bar:** Vertical selector (Life Sciences, Manufacturing, Software) + search
- **Pack Grid:** Cards with icon, name, description, usage count, activation CTA
- **Preview Panel:** Expandable side drawer with formula preview and variables
- **My Packs Section:** Already-activated packs with configuration status

**5. Key Interactions**
- Click pack card to expand preview
- Activate button triggers onboarding wizard
- Search filters in real-time
- Filter pills for multi-select categories

**6. State Transitions**
- Browse → Preview → Activate → Configuration
- Activation pending: Shows spinner and progress
- Activation complete: Confetti + redirect to Value Tree
- Already activated: "Go to Model" button instead of "Activate"

**7. Data + Agent Behavior**
- `useValuePacks()` fetches from Layer 3 knowledge API
- Agents pre-compute relevance scores based on user's industry
- Data: pack metadata, formulas, variable mappings, ontology references

**8. Output / Next Step**
- Activated pack creates entities in user's knowledge graph
- Redirect to Value Tree Explorer for the new model
- Trigger onboarding wizard for variable binding

**9. Edge Cases**
- No packs for industry: Show "Request Custom Pack" CTA
- Activation fails: Show error with retry or contact support
- Duplicate activation: Prompt to create copy or replace

---

## My Models **[standard]**

**1. Context**
Personal workspace containing all value models the user has created or customized.

**2. Objective**
Manage owned models, track their status, and organize by project or account.

**3. Mental Model**
A project workspace or file manager. Folders, status labels, and quick actions on owned content.

**4. Layout**
- **Header:** Create Model button + view toggle (grid/list)
- **Model List:** Name, type, last modified, status badge, actions menu
- **Folder Sidebar:** User-defined collections (collapsible)
- **Search/Filter:** Full-text search + status filters

**5. Key Interactions**
- Click model name to open Value Tree Explorer
- Actions menu: Rename, duplicate, archive, share
- Drag models to folders (if folders enabled)
- Bulk select for batch operations

**6. State Transitions**
- Create → Empty form with template selection
- Edit → Value Tree Explorer in edit mode
- Archive → Confirmation dialog + status change
- Share → Permission dialog with link generation

**7. Data + Agent Behavior**
- User-scoped entities from Layer 3
- Agents track model usage and suggest optimizations
- Data: entity IDs, model metadata, modification history

**8. Output / Next Step**
- Open model in Value Tree Explorer
- Generate shareable link
- Export model definition (JSON)

**9. Edge Cases**
- No models: Empty state with "Create from Template" CTA
- Large collections: Virtualized scrolling + pagination
- Shared models: Indicate owner + permission level

---

## Pack Authoring **[admin]**

**1. Context**
Studio environment for creating, editing, and publishing Value Packs for tenant or public distribution.

**2. Objective**
Enable pack authors to bundle formulas, variables, ontologies, and documentation into distributable packages.

**3. Mental Model**
An IDE for value models. File explorer, editor panes, preview mode, and publish controls.

**4. Layout**
- **Pack Navigator:** Tree view of pack structure (formulas/, variables/, ontology/, docs/)
- **Editor Zone:** JSON/YAML editor with validation
- **Preview Panel:** Live render of how pack appears in Library
- **Toolbar:** Save, Validate, Publish, Version controls

**5. Key Interactions**
- Click file in navigator to open in editor
- Drag files to reorganize
- Ctrl+S to save (with auto-save indicator)
- Validate button runs schema checks
- Publish opens semver dialog and distribution options

**6. State Transitions**
- Draft → Saved → Validated → Published
- Validation errors highlight lines in editor
- Publish creates immutable version
- Edit published pack creates new draft (semver bump)

**7. Data + Agent Behavior**
- Schema validation against `contracts/jsonschema/`
- Agents suggest formula optimizations and variable bindings
- Data: pack manifest, formula definitions, ontology JSON

**8. Output / Next Step**
- Published pack appears in Library for tenant users
- Version history tracked in governance log
- Rollback option for published versions

**9. Edge Cases**
- Invalid schema: Block publish with detailed error list
- Name collision: Prompt for rename or version bump
- Orphaned variables: Warning when formulas reference undefined vars

---

# Discover

## Accounts **[standard]**

**1. Context**
CRM-style account management for tracking companies, opportunities, and related entities.

**2. Objective**
Maintain account records, view associated value models, and trigger account-scoped workflows.

**3. Mental Model**
A lightweight CRM. Account cards, detail views, and related records.

**4. Layout**
- **Account List:** Table with name, industry, status, last activity
- **Detail Panel:** Slide-out with account details, contacts, linked models
- **Action Bar:** New Account, Import, Export, Bulk Actions
- **Filter Chips:** Industry, status, last modified ranges

**5. Key Interactions**
- Click row to expand detail panel
- Create account opens modal with form
- Import button triggers CSV upload flow
- Link model button shows available models

**6. State Transitions**
- List → Detail → Edit → Save
- Import → Upload → Map Fields → Confirm → Import Complete
- Link Model → Model Selector → Bind Variables → Confirm

**7. Data + Agent Behavior**
- Account entities from Layer 3
- Agents enrich accounts with external data (when configured)
- Data: account properties, relationships, linked entities

**8. Output / Next Step**
- Navigate to account-specific Business Case
- Trigger extraction for account data
- Export account list with linked metrics

**9. Edge Cases**
- Duplicate accounts: Merge suggestion dialog
- Import errors: Row-level error report with download
- Large accounts: Pagination on related records

---

## Ingestion Jobs **[standard]**

**1. Context**
Monitor and manage data ingestion pipelines from external sources into the knowledge graph.

**2. Objective**
Track ingestion status, review errors, and re-trigger failed jobs.

**3. Mental Model**
A pipeline dashboard. Job cards with progress bars, status indicators, and logs.

**4. Layout**
- **Job Queue:** Active and recent jobs with status badges
- **Job Detail:** Source, destination, record count, error log
- **Filter Controls:** Status, source type, date range
- **Actions:** Retry, Cancel, Schedule

**5. Key Interactions**
- Click job card to expand details and logs
- Retry button re-enqueues failed jobs
- Cancel sends stop signal to running job
- Schedule opens cron expression builder

**6. State Transitions**
- Pending → Running → Completed | Failed | Cancelled
- Failed → Retry → Pending
- Click log entry opens full log viewer

**7. Data + Agent Behavior**
- Layer 1 ingestion API provides job status
- Agents classify errors and suggest fixes
- Real-time updates via polling or SSE
- Data: job metadata, progress, error logs, record counts

**8. Output / Next Step**
- Retry failed jobs
- Navigate to extracted entities from completed jobs
- Download error reports for external analysis

**9. Edge Cases**
- Long-running jobs: Show elapsed time + estimated completion
- Stalled jobs: Auto-detect and surface warning
- High error rate: Escalate to admin notification

---

## Extraction Engine **[advanced]**

**1. Context**
Power-user interface for configuring and monitoring LLM-based data extraction pipelines.

**2. Objective**
Direct control over extraction prompts, entity recognition, and knowledge graph population.

**3. Mental Model**
A workflow orchestrator. Configure inputs, see real-time extraction streams, validate outputs.

**4. Layout**
- **Configuration Panel:** Source selection, prompt template, entity types
- **Live Stream:** Real-time extraction log with entity preview
- **Results Table:** Extracted entities with confidence scores
- **Control Bar:** Start, Pause, Stop, Configure buttons

**5. Key Interactions**
- Select source from configured integrations
- Edit prompt template with variable insertion
- Start extraction begins streaming process
- Click entity in stream to inspect and edit

**6. State Transitions**
- Idle → Configuring → Running → Paused | Completed | Failed
- Running: Live log scrolls with color-coded entries
- Completed: Summary stats with entity breakdown
- Failed: Error details with retry options

**7. Data + Agent Behavior**
- `useWorkflowSSE()` streams extraction progress
- Layer 2 extraction service processes documents
- Agents validate entity confidence and flag low-confidence extractions
- Data: raw documents, extracted entities, confidence scores, logs

**8. Output / Next Step**
- Extracted entities written to Layer 3 knowledge graph
- Navigate to Graph Explorer to review relationships
- Export extraction report with metrics

**9. Edge Cases**
- Source unavailable: Display connection error with diagnostic link
- Low confidence extractions: Queue for manual review
- Rate limiting: Display backoff timer

---

## Knowledge Model **[advanced]**

**1. Context**
Container section for navigating and understanding the knowledge graph structure.

**2. Objective**
Explore entities, relationships, and ontologies that define the domain model.

**3. Mental Model**
A database schema explorer meets graph navigator. Tables of entities and visual relationship maps.

**4. Layout**
- **Sub-navigation:** Entity Browser | Graph Explorer | Ontology Editor
- **Context Header:** Current view title + search/filter
- **Content Zone:** View-specific content (table, graph, or form)

---

### Entity Browser **[advanced]**

**1. Context**
Tabular view of all entities in the knowledge graph with filtering and search.

**2. Objective**
Find specific entities, review properties, and navigate to related records.

**3. Mental Model**
A database table browser with rich filters and relationship navigation.

**4. Layout**
- **Filter Bar:** Entity type selector, property filters, full-text search
- **Data Table:** Paginated rows with sortable columns
- **Detail Drawer:** Slide-out entity detail with relationships
- **Export Button:** CSV/JSON export of filtered results

**5. Key Interactions**
- Filter pills add/remove criteria
- Column headers sort (click) or filter (hover menu)
- Click row to open detail drawer
- Relationship links navigate to related entity

**6. State Transitions**
- Filter change → Table refresh with loading state
- Row click → Drawer animation with entity detail
- Export → Download dialog with format selection

**7. Data + Agent Behavior**
- Layer 3 knowledge API serves entity data
- Agents suggest filters based on common queries
- Data: entity properties, types, relationships, provenance

**8. Output / Next Step**
- Navigate to entity detail page
- Export filtered results
- Trigger entity-scoped workflows

---

### Graph Explorer **[advanced]**

**1. Context**
Interactive visualization of the knowledge graph showing entities as nodes and relationships as edges.

**2. Objective**
Visual exploration of graph topology, community detection, and relationship patterns.

**3. Mental Model**
A network map. Zoom, pan, click nodes to expand, see connection density.

**4. Layout**
- **Canvas Zone:** D3/Canvas-based graph visualization (centered)
- **Control Panel:** Zoom, layout algorithm selector, filter controls
- **Legend:** Color coding for entity types
- **Inspector Panel:** Selected node details and neighbors

**5. Key Interactions**
- Drag canvas to pan, scroll to zoom
- Click node to select and show details
- Double-click node to expand neighbors
- Right-click for context menu (hide, focus, export)
- Layout buttons reorganize graph (force-directed, circular, hierarchical)

**6. State Transitions**
- Empty → Loading spinner → Graph render
- Node click: Highlight node + populate inspector
- Zoom change: Re-render with level-of-detail optimization
- Filter change: Fade/hide filtered nodes

**7. Data + Agent Behavior**
- Layer 3 graph API provides node/edge data
- Agents compute community clusters and centrality metrics
- Canvas uses D3 force simulation for layout
- Data: nodes (entities), edges (relationships), metadata

**8. Output / Next Step**
- Navigate to selected entity detail
- Export graph view as image or graph data
- Run graph algorithms (shortest path, clustering)

**9. Edge Cases**
- Large graphs (>1000 nodes): Progressive loading + level-of-detail
- Dense clusters: Zoom to expand and prevent node overlap
- No relationships: Show isolated nodes with import suggestion

---

### Ontology Editor **[advanced]**

**1. Context**
Interface for defining entity types, properties, and relationship schemas.

**2. Objective**
Extend or customize the domain model by editing ontology definitions.

**3. Mental Model**
A schema designer. Class hierarchy, property definitions, validation rules.

**4. Layout**
- **Type Tree:** Hierarchical view of entity types (left sidebar)
- **Property Editor:** Form for type properties and constraints (center)
- **Relationship Map:** Visual of type relationships (right panel)
- **Toolbar:** New Type, Save, Validate, Import/Export

**5. Key Interactions**
- Click type in tree to edit
- Add property button opens property form
- Drag types to reorganize hierarchy
- Validate checks for circular references and conflicts

**6. State Transitions**
- Browse → Edit → Modified → Saved | Validation Error
- New Type → Template selection → Editor
- Import → File upload → Validation → Merge/Replace

**7. Data + Agent Behavior**
- Ontology JSON from packs or Layer 3
- Agents suggest property types based on usage patterns
- Validation ensures referential integrity
- Data: entity types, properties, constraints, inheritance

**8. Output / Next Step**
- Saved ontology updates graph schema
- Publish creates new pack version
- Export JSON for external use

**9. Edge Cases**
- Delete in-use type: Block with usage count + force option
- Circular inheritance: Validation error with path highlight
- Breaking changes: Warn with impact analysis

---

## Integrations **[admin]**

**1. Context**
Configuration hub for external data sources, APIs, and service connections.

**2. Objective**
Set up and manage integrations with CRMs, data warehouses, and external APIs.

**3. Mental Model**
An integration marketplace. Browse connectors, configure credentials, test connections.

**4. Layout**
- **Integration Grid:** Available connectors with status indicators
- **Configuration Panel:** Form for selected integration
- **Test Area:** Connection test with diagnostic output
- **Active Integrations:** List of configured connections

**5. Key Interactions**
- Click connector tile to configure
- OAuth flows open popup for authorization
- Test button validates credentials
- Enable/disable toggle controls active state

**6. State Transitions**
- Unconfigured → Configured → Tested → Active | Failed
- OAuth → External auth → Callback → Token stored
- Test failure → Diagnostic output with fix suggestions

**7. Data + Agent Behavior**
- Integration configs stored in Layer 1/2
- Agents monitor integration health and retry failed syncs
- Data: credentials (encrypted), connection settings, sync schedules

**8. Output / Next Step**
- Active integration available in Extraction Engine
- Sync jobs appear in Ingestion Jobs
- Health status visible in Command Center

**9. Edge Cases**
- Credential expiration: Alert with re-auth link
- Rate limiting: Backoff with manual retry option
- Scope changes: Re-authorization prompt for new permissions

---

## Source Configuration **[admin]**

**1. Context**
Detailed configuration for scraping targets, API endpoints, and data source parameters.

**2. Objective**
Fine-grained control over how external sources are accessed and parsed.

**3. Mental Model**
A network configuration panel. URLs, headers, selectors, and schedules.

**4. Layout**
- **Source List:** Configured targets with health status
- **Config Form:** URL, method, headers, body, selectors
- **Schedule Panel:** Cron expression or interval settings
- **Preview Area:** Live test fetch with parsed output

**5. Key Interactions**
- Add source opens blank configuration
- Test fetch button executes sample request
- Selector fields highlight matching elements in preview
- Save validates and stores configuration

**6. State Transitions**
- New → Configure → Test → Save → Active
- Edit → Modified → Save → Update
- Delete → Confirm → Remove

**7. Data + Agent Behavior**
- Layer 1 ingestion stores configurations
- Agents suggest CSS selectors from sample pages
- Data: source URLs, credentials, selectors, schedules

**8. Output / Next Step**
- Source available in Ingestion Jobs
- Trigger manual extraction
- Export configuration for migration

---

# Model

## Value Studio **[advanced]**

**1. Context**
Container for value modeling tools: tree exploration, data normalization, and formula authoring.

**2. Objective**
Build, refine, and validate quantitative value models that power business cases.

**3. Mental Model**
A modeling workbench. Explore structures, clean data, write formulas, see results.

**4. Layout**
- **Sub-navigation:** Explorer | Normalization | Formula Builder
- **Breadcrumbs:** Current model path
- **Content Zone:** View-specific tools

---

### Explorer **[advanced]**

**1. Context**
Interactive visualization and editing of value trees showing how metrics roll up to value outcomes.

**2. Objective**
Navigate value hierarchies, understand metric relationships, and identify optimization opportunities.

**3. Mental Model**
An org chart for value. Parent nodes are outcomes, children are drivers, leaf nodes are metrics.

**4. Layout**
- **Tree Canvas:** Hierarchical visualization with collapsible nodes
- **Node Inspector:** Properties, formula reference, data source
- **Toolbar:** Zoom, layout toggle (tree/radial/list), filter
- **Path Tracer:** Highlight upstream/downstream dependencies

**5. Key Interactions**
- Click node to expand/collapse children
- Drag nodes to reorganize (with validation)
- Double-click to edit node properties
- Hover for quick stat tooltip
- Trace mode highlights value flow

**6. State Transitions**
- Browse → Select → Edit → Save
- Drag node → Validation → Reorder | Reject
- Filter → Partial tree render → Clear → Full tree

**7. Data + Agent Behavior**
- Layer 3 value tree API
- Agents compute rollup values and flag inconsistencies
- Data: tree structure, node formulas, variable bindings, computed values

**8. Output / Next Step**
- Edit node in Formula Builder
- Run what-if analysis
- Export tree as presentation graphic

---

### Normalization **[advanced]**

**1. Context**
Data cleaning and transformation interface for preparing raw data for value calculations.

**2. Objective**
Map, clean, and normalize variables from diverse sources into consistent formats.

**3. Mental Model**
A data wrangling tool. Column mapping, transformation rules, quality checks.

**4. Layout**
- **Source Preview:** Sample data from selected source (left)
- **Mapping Table:** Source column → Variable → Transformation rule (center)
- **Quality Panel:** Missing values, outliers, type mismatches (right)
- **Action Bar:** Auto-map, Validate, Apply

**5. Key Interactions**
- Drag source column to variable slot
- Click rule cell to edit transformation
- Auto-map attempts fuzzy matching
- Validate runs quality checks

**6. State Transitions**
- Unmapped → Mapping → Validated → Applied
- Validation error → Highlight cells → Fix → Re-validate

**7. Data + Agent Behavior**
- Agents suggest mappings based on column names
- Quality rules from Variable Registry
- Data: source schemas, variable definitions, transformation history

**8. Output / Next Step**
- Applied mappings update value tree inputs
- Normalized data available for formulas
- Quality report exported

---

### Formula Builder **[advanced]**

**1. Context**
Visual interface for authoring, testing, and debugging value calculation formulas.

**2. Objective**
Create and edit formulas with live preview, validation, and version control.

**3. Mental Model**
A smart calculator with memory. Formula editor, variable picker, live results, history.

**4. Layout**
- **Editor Zone:** Monaco-based formula editor with syntax highlighting
- **Variable Palette:** Searchable list of available variables
- **Test Panel:** Input values and computed result
- **History Sidebar:** Previous versions with diff view

**5. Key Interactions**
- Type formula with autocomplete for variables and functions
- Drag variable from palette to insert
- Test button runs calculation with sample inputs
- Save creates new version with changelog

**6. State Transitions**
- Edit → Validating → Valid | Invalid
- Valid → Test → Results displayed
- Save → Version created → Available in governance

**7. Data + Agent Behavior**
- `useFormulas()` hooks for formula CRUD
- Agents suggest optimizations and detect common errors
- Governance workflow for approval
- Data: formula definitions, variables, test cases, versions

**8. Output / Next Step**
- Submit for approval (triggers governance workflow)
- Deploy to value tree nodes
- Export formula definition

**9. Edge Cases**
- Circular reference: Block with dependency graph
- Division by zero: Runtime warning in test panel
- Unknown variable: Suggest similar names

---

# Deliver

## Business Cases **[standard]**

**1. Context**
ROI analysis workspace where value models are applied to specific accounts or opportunities.

**2. Objective**
Quantify value delivery, generate proposals, and track case status through sales cycles.

**3. Mental Model**
A deal room. Value calculations, proposal documents, stakeholder tracking.

**4. Layout**
- **Case List:** Cards or table with status, account, value, last activity
- **Case Detail:** Value summary, inputs, assumptions, outputs
- **Proposal Preview:** Generated document with charts and text
- **Actions:** Edit, Generate PDF, Share, Convert to Opportunity

**5. Key Interactions**
- Click case to open detail
- Edit inputs opens form with value tree binding
- Generate creates PDF proposal
- Share opens email/link dialog

**6. State Transitions**
- Draft → Active → Pending Approval → Approved | Rejected
- Input change → Recalculation → Updated results
- Generate → Rendering → Download ready

**7. Data + Agent Behavior**
- `useBusinessCases()` fetches case data
- Agents generate narrative text from value outputs
- Data: case metadata, value calculations, proposals, activity history

**8. Output / Next Step**
- PDF proposal download
- CRM opportunity creation (if integrated)
- Share link for stakeholder review

---

## Opportunity Finder **[standard]**

**1. Context**
AI-assisted tool for identifying whitespace and upsell opportunities within accounts.

**2. Objective**
Surface untapped value potential and recommend next-best actions.

**3. Mental Model**
A sales intelligence dashboard. Opportunity cards, fit scores, and recommended actions.

**4. Layout**
- **Filter Bar:** Account, product area, opportunity type
- **Opportunity Grid:** Cards with title, account, potential value, confidence
- **Detail Drawer:** Evidence, recommended actions, related cases
- **Action Buttons:** Create Case, Dismiss, Schedule Follow-up

**5. Key Interactions**
- Filter to narrow opportunities
- Click card for details and evidence
- Create case pre-fills opportunity data
- Dismiss removes from view (recoverable)

**6. State Transitions**
- Detected → Reviewed → Case Created | Dismissed
- Case created links opportunity to business case

**7. Data + Agent Behavior**
- Agents analyze account data against value models
- Scoring based on fit, timing, and accessibility
- Data: opportunities, scores, evidence, recommendations

**8. Output / Next Step**
- Create business case from opportunity
- Export opportunity list
- Trigger outreach workflow

---

## Whitespace Analysis **[advanced]**

**1. Context**
Deep analytical view of account coverage showing deployed vs. available value models.

**2. Objective**
Identify gaps in value realization and plan expansion strategies.

**3. Mental Model**
A coverage map. Matrix of accounts vs. value models with adoption heatmap.

**4. Layout**
- **Matrix View:** Accounts (rows) × Value Packs (columns) with adoption status
- **Summary Panel:** Coverage stats, penetration rates, opportunity totals
- **Drill-down:** Click cell to see detailed deployment status
- **Export:** Full matrix or filtered views

**5. Key Interactions**
- Hover cell for quick status tooltip
- Click cell for detailed breakdown
- Filter accounts by industry, size, region
- Toggle between pack view and metric view

**6. State Transitions**
- Overview → Drill-down → Account detail
- Filter → Matrix refresh with loading state

**7. Data + Agent Behavior**
- Aggregated data from Layer 3
- Agents compute penetration rates and recommend priority accounts
- Data: account list, pack deployments, metric coverage

**8. Output / Next Step**
- Export coverage report
- Navigate to specific account business case
- Create expansion opportunity

---

## Agent Dashboard **[advanced]**

**1. Context**
Monitoring and control interface for AI agent workflows and automation tasks.

**2. Objective**
Track agent activity, review decisions, and intervene when necessary.

**3. Mental Model**
A mission control for AI workers. Task queue, performance metrics, human-in-the-loop requests.

**4. Layout**
- **Agent Overview:** List of active agents with status and task counts
- **Task Queue:** Pending, running, and completed tasks with priorities
- **Intervention Panel:** Human review requests with approve/reject options
- **Performance Charts:** Success rates, latency, throughput over time

**5. Key Interactions**
- Click agent to see detailed task history
- Approve/reject pending interventions
- Pause/resume agent task processing
- Configure agent parameters

**6. State Transitions**
- Pending → Running → Completed | Failed | Awaiting Review
- Review → Approved → Continues | Rejected → Rollback

**7. Data + Agent Behavior**
- Layer 4 agent API provides task status
- Human-in-the-loop triggers for low-confidence decisions
- Data: agent states, tasks, decisions, interventions, metrics

**8. Output / Next Step**
- Approve pending decisions
- Navigate to affected entity for context
- Export agent performance report

---

## Interactive Explorer **[advanced]**

**1. Context**
Conversational interface for exploring value models and business cases through natural language.

**2. Objective**
Enable non-technical users to query complex models and get visual answers.

**3. Mental Model**
A chat with charts. Ask questions, get visualizations, drill down through conversation.

**4. Layout**
- **Chat Interface:** Message history with user and agent responses
- **Visualization Zone:** Dynamic charts and graphs based on queries
- **Suggestion Chips:** Common questions and next-step prompts
- **Context Sidebar:** Current model/account context

**5. Key Interactions**
- Type natural language query
- Click suggestion chip for quick question
- Click visualization to expand/detach
- Save conversation as report

**6. State Transitions**
- Input → Processing → Response (with visualization)
- Follow-up questions maintain context
- Save creates static report from conversation

**7. Data + Agent Behavior**
- Layer 4 conversational agent processes queries
- NL-to-SQL/graph translation
- Agents generate appropriate visualizations
- Data: conversation history, generated queries, result sets

**8. Output / Next Step**
- Export conversation as PDF
- Navigate to referenced entity pages
- Share conversation link

---

# Evidence

## Decision Traces **[standard]**

**1. Context**
Audit trail of all AI-assisted decisions with full provenance and rationale.

**2. Objective**
Provide transparency into how conclusions were reached and enable accountability.

**3. Mental Model**
A flight recorder. Timeline of decisions, inputs, model versions, and confidence levels.

**4. Layout**
- **Trace List:** Chronological decisions with type, account, timestamp, outcome
- **Trace Detail:** Step-by-step execution log with inputs/outputs
- **Filter Controls:** Date range, decision type, account, agent
- **Export:** Full trace or summary report

**5. Key Interactions**
- Click trace to expand detail
- Step through execution timeline
- View input data at each step
- Compare traces side-by-side

**6. State Transitions**
- List → Detail → Step inspection
- Export → Format selection → Download

**7. Data + Agent Behavior**
- Layer 5 ground truth store provides trace data
- Agents annotate traces with confidence and alternatives considered
- Data: execution graphs, inputs, outputs, model versions, timestamps

**8. Output / Next Step**
- Export trace for compliance review
- Navigate to source entity
- Flag trace for investigation

---

## Export Reports **[standard]**

**1. Context**
Self-service report generation for sharing insights with external stakeholders.

**2. Objective**
Create formatted documents, presentations, and data exports from platform content.

**3. Mental Model**
A report builder. Select content, choose format, customize branding, generate.

**4. Layout**
- **Content Selector:** Tree of available reports and visualizations
- **Format Options:** PDF, PowerPoint, Excel, CSV
- **Branding Panel:** Logo, colors, header/footer customization
- **Preview:** Live render of final output

**5. Key Interactions**
- Check items to include in report
- Drag to reorder sections
- Upload logo for branding
- Generate triggers async rendering

**6. State Transitions**
- Select → Configure → Preview → Generate → Download
- Large reports show progress bar

**7. Data + Agent Behavior**
- Report service aggregates content
- Agents suggest relevant content based on recipient role
- Data: selected content, templates, branding, generated files

**8. Output / Next Step**
- Download generated report
- Schedule recurring generation
- Share via email integration

---

## Lineage Explorer **[advanced]**

**1. Context**
End-to-end data lineage visualization showing how raw data flows through to business decisions.

**2. Objective**
Understand data provenance, track impact of source changes, and ensure data quality.

**3. Mental Model**
A supply chain map. Sources → transformations → entities → calculations → decisions.

**4. Layout**
- **Lineage Graph:** Horizontal flow from sources to outputs
- **Node Types:** Sources (blue), Transformations (green), Entities (purple), Decisions (amber)
- **Impact Panel:** Highlight downstream affected by selected node
- **Version Timeline:** Historical versions of lineage

**5. Key Interactions**
- Click node to see details and properties
- Trace forward/downstream from any point
- Trace backward/upstream to find data sources
- Filter by time range or entity type

**6. State Transitions**
- Overview → Focus → Trace → Detail
- Time slider animates lineage evolution

**7. Data + Agent Behavior**
- Layer 3 provenance API
- Agents detect lineage gaps and suggest connections
- Data: source records, transformations, dependencies, versions

**8. Output / Next Step**
- Export lineage diagram
- Navigate to source configuration
- Create data quality alert

---

## Compliance Reports **[advanced]**

**1. Context**
Pre-built and custom reports for regulatory compliance and internal governance.

**2. Objective**
Demonstrate adherence to policies, generate audit evidence, and track controls.

**3. Mental Model**
A compliance dashboard. Control status, policy adherence, evidence packages.

**4. Layout**
- **Report Library:** Pre-built compliance templates (SOC2, GDPR, etc.)
- **Control Matrix:** List of controls with status and evidence
- **Evidence Panel:** Linked artifacts proving control effectiveness
- **Schedule:** Automated generation and distribution settings

**5. Key Interactions**
- Select report template to generate
- Link evidence to controls
- Schedule recurring generation
- Export for auditor review

**6. State Transitions**
- Template → Configure → Generate → Review → Distribute
- Control status: Compliant → At Risk → Non-compliant

**7. Data + Agent Behavior**
- Governance data from Layer 4
- Agents collect evidence from across platform
- Data: controls, policies, evidence, attestations

**8. Output / Next Step**
- Export compliance package
- Submit to audit workflow
- Trigger remediation for failed controls

---

## Full Change Log **[admin]**

**1. Context**
System-wide audit log of all configuration and data changes.

**2. Objective**
Track who changed what, when, and why for full accountability.

**3. Mental Model**
An immutable journal. Chronological changes with actor, action, before/after.

**4. Layout**
- **Log Table:** Timestamp, actor, action, entity type, entity ID, change summary
- **Detail Drawer:** Full change payload with before/after diff
- **Filter Bar:** Actor, entity type, date range, action type
- **Export:** Full log or filtered subset

**5. Key Interactions**
- Filter to narrow results
- Click row for detail diff
- Export for external audit
- Bookmark frequent queries

**6. State Transitions**
- Filter → Table refresh
- Click → Drawer animation with diff

**7. Data + Agent Behavior**
- Layer 3/4 audit APIs
- Structured logging from all layers
- Data: audit events, actor info, payloads, timestamps

**8. Output / Next Step**
- Export audit trail
- Navigate to affected entity
- Create incident from suspicious activity

---

# Govern

## Content Governance **[admin]**

**1. Context**
Container section for managing formula lifecycle, benchmark policies, and approval workflows.

**2. Objective**
Ensure quality, consistency, and compliance of all analytical content.

**3. Mental Model**
A publishing house. Drafts, reviews, approvals, and published catalog.

**4. Layout**
- **Sub-navigation:** Formula Registry | Version History | Approval Queue | Benchmark Policies
- **Dashboard Cards:** Pending approvals, recent changes, policy violations
- **Content Zone:** View-specific management interface

---

### Formula Registry **[admin]**

**1. Context**
Central catalog of all formulas with metadata, status, and governance state.

**2. Objective**
Manage formula definitions, track versions, and control publication.

**3. Mental Model**
A library catalog. Searchable index with checkout status and location.

**4. Layout**
- **Registry Table:** Formula name, owner, status, version, last modified
- **Filter Bar:** Status, owner, pack, data source
- **Bulk Actions:** Approve, deprecate, assign
- **Detail Panel:** Formula definition, dependencies, usage stats

**5. Key Interactions**
- Click row to view formula detail
- Status filters for workflow management
- Bulk select for mass operations
- Export registry as CSV/JSON

**6. State Transitions**
- Draft → Submitted → Under Review → Approved | Rejected
- Approved → Published → Active | Deprecated

**7. Data + Agent Behavior**
- Layer 4 governance API
- Agents detect unused formulas and suggest deprecation
- Data: formula definitions, versions, owners, approvals

**8. Output / Next Step**
- Open formula in Formula Builder
- Submit for approval
- Deprecate with replacement suggestion

---

### Version History **[admin]**

**1. Context**
Immutable history of all formula versions with diff and rollback capabilities.

**2. Objective**
Track formula evolution, understand changes, and recover previous versions.

**3. Mental Model**
A version control system. Commits, diffs, branches (variants), tags (releases).

**4. Layout**
- **Version List:** Chronological versions with author, message, timestamp
- **Diff View:** Side-by-side or inline comparison
- **Rollback Panel:** Select version to restore
- **Branch View:** Formula variants and their lineage

**5. Key Interactions**
- Select two versions to compare
- Click version to view full definition
- Rollback creates new version (never deletes history)
- Tag version as release

**6. State Transitions**
- Compare → Diff view with additions/removals highlighted
- Rollback → Confirm → New version created → Published

**7. Data + Agent Behavior**
- Version store from Layer 4
- Agents flag breaking changes in diffs
- Data: versioned formulas, diffs, authors, tags

**8. Output / Next Step**
- Export version history
- Restore previous version
- Create branch from historical version

---

### Approval Queue **[admin]**

**1. Context**
Workflow management for content pending governance review.

**2. Objective**
Review, approve, or reject formula submissions with structured feedback.

**3. Mental Model**
An inbox. Items awaiting action with priority, age, and assignment.

**4. Layout**
- **Queue List:** Submitter, item type, submitted date, priority, status
- **Review Panel:** Item details, diff from previous, test results
- **Action Bar:** Approve, Reject, Request Changes, Reassign
- **Comments Thread:** Discussion between submitter and reviewer

**5. Key Interactions**
- Click item to open review panel
- Approve publishes to registry
- Reject with required feedback
- Request changes returns to submitter

**6. State Transitions**
- Submitted → Assigned → Under Review → Approved | Rejected | Changes Requested
- Changes Requested → Revised → Re-submitted

**7. Data + Agent Behavior**
- Workflow engine from Layer 4
- Agents auto-approve low-risk changes
- Data: submissions, reviewers, decisions, comments

**8. Output / Next Step**
- Approved item moves to registry
- Rejected item returns to owner
- Changes requested opens task for submitter

---

### Benchmark Policies **[admin]**

**1. Context**
Configuration of industry benchmarks and comparison policies.

**2. Objective**
Define how external benchmarks are sourced, validated, and applied to value calculations.

**3. Mental Model**
A policy handbook. Rules for benchmark usage, approval levels, and override conditions.

**4. Layout**
- **Policy List:** Benchmark categories with status and coverage
- **Editor Panel:** Source, refresh schedule, validation rules
- **Preview:** Sample benchmark data with quality indicators
- **Override Log:** History of manual benchmark adjustments

**5. Key Interactions**
- Click policy to edit
- Test button validates source connectivity
- Override opens justification form
- Schedule defines automatic refresh

**6. State Transitions**
- Draft → Active | Inactive
- Override → Logged → Reviewed

**7. Data + Agent Behavior**
- Benchmark service from Layer 2
- Agents validate benchmark freshness and outliers
- Data: policies, sources, schedules, overrides, logs

**8. Output / Next Step**
- Active policy used in formula calculations
- Override triggers approval workflow
- Export policy documentation

---

## Data Governance **[admin]**

**1. Context**
Container for managing variable definitions, source bindings, and data quality rules.

**2. Objective**
Ensure data consistency, quality, and proper lineage across all calculations.

**3. Mental Model**
A data dictionary with enforcement. Definitions, mappings, constraints, quality checks.

**4. Layout**
- **Sub-navigation:** Variable Registry | Source Bindings | Quality Rules
- **Dashboard:** Data quality scores, unmapped variables, binding health
- **Content Zone:** Selected governance view

---

### Variable Registry **[admin]**

**1. Context**
Master catalog of all variables with definitions, types, and metadata.

**2. Objective**
Maintain consistent variable definitions across formulas and packs.

**3. Mental Model**
A dictionary. Terms, definitions, synonyms, and usage examples.

**4. Layout**
- **Variable Table:** Name, type, description, usage count, status
- **Filter Bar:** Type, pack, data source, binding status
- **Detail Panel:** Full definition, formula references, bindings
- **Actions:** Create, Edit, Deprecate, Merge

**5. Key Interactions**
- Search variables by name or description
- Click to view usage across formulas
- Edit opens definition form
- Deprecate with replacement mapping

**6. State Transitions**
- Draft → Active → Deprecated
- Merge → Select target → Update references → Archive source

**7. Data + Agent Behavior**
- Layer 3 variable catalog
- Agents detect duplicate or similar variables
- Data: variable definitions, types, bindings, usage stats

**8. Output / Next Step**
- Updated definition propagates to formulas
- Deprecation triggers migration workflow
- Export registry documentation

---

### Source Bindings **[admin]**

**1. Context**
Mapping interface connecting variable definitions to actual data sources.

**2. Objective**
Define how abstract variables are populated from concrete data sources.

**3. Mental Model**
Adapter configuration. Source connection, field mapping, transformation rules.

**4. Layout**
- **Binding List:** Variable, source, field path, last sync, health
- **Binding Editor:** Source selection, field picker, transformation
- **Test Panel:** Live fetch with sample output
- **Sync Log:** History of binding executions

**5. Key Interactions**
- Click binding to edit configuration
- Field picker browses source schema
- Test validates binding works
- Sync Now triggers manual refresh

**6. State Transitions**
- Unconfigured → Partial → Complete → Active | Failed
- Failed → Diagnose → Fix → Test → Active

**7. Data + Agent Behavior**
- Layer 1/2 binding service
- Agents suggest bindings based on field names
- Data: binding configs, source references, sync history

**8. Output / Next Step**
- Active binding populates variables for formulas
- Failed binding alerts data owners
- Export binding documentation

---

### Quality Rules **[admin]**

**1. Context**
Definition and monitoring of data quality constraints and validation rules.

**2. Objective**
Ensure data integrity through automated checks and alerts.

**3. Mental Model**
A testing framework. Rules, assertions, test runs, failure reports.

**4. Layout**
- **Rule List:** Rule name, scope, severity, status, last run
- **Rule Editor:** Condition builder, severity, notification settings
- **Results Panel:** Recent rule executions with pass/fail counts
- **Alert Config:** Notification destinations and thresholds

**5. Key Interactions**
- Click rule to view recent results
- Edit opens condition builder
- Run Now executes rule ad-hoc
- Severity controls alert routing

**6. State Transitions**
- Draft → Active → Paused | Archived
- Run → Processing → Results (Pass/Warning/Fail)

**7. Data + Agent Behavior**
- Quality engine from Layer 2/3
- Agents suggest rules based on data patterns
- Data: rule definitions, executions, violations, alerts

**8. Output / Next Step**
- Violations trigger notifications
- Quality scores affect data trust indicators
- Export quality report

---

## Access Control **[admin]**

**1. Context**
Container for role-based access control, team management, and API credential governance.

**2. Objective**
Manage who can access what, with proper segregation and audit trails.

**3. Mental Model**
A security command center. Permissions, groups, credentials, activity logs.

**4. Layout**
- **Sub-navigation:** Roles & Permissions | Teams | API Keys
- **Dashboard:** Access stats, recent grants/revocations, policy violations
- **Content Zone:** Selected access management view

---

### Roles & Permissions **[admin]**

**1. Context**
Management of user roles and their associated permission sets.

**2. Objective**
Define and assign granular permissions across platform features and data.

**3. Mental Model**
A permission matrix. Roles (rows) × Permissions (columns) with checkboxes.

**4. Layout**
- **Role List:** Built-in and custom roles with user counts
- **Permission Matrix:** Feature/data permissions with role assignments
- **User Assignment:** Add/remove users from roles
- **Audit Panel:** Recent permission changes

**5. Key Interactions**
- Click role to edit permissions
- Toggle permissions in matrix
- Search users for assignment
- Clone role as template

**6. State Transitions**
- Edit → Modified → Save → Propagated to users
- Assign → User gains permissions immediately

**7. Data + Agent Behavior**
- Identity service from `shared/identity`
- Agents detect overprivileged users and suggest least-privilege
- Data: roles, permissions, assignments, audit logs

**8. Output / Next Step**
- Permission changes apply immediately
- Export role documentation
- Trigger access review workflow

---

### Teams **[admin]**

**1. Context**
Organizational unit management for grouping users and resources.

**2. Objective**
Model organizational structure and scope access by team membership.

**3. Mental Model**
An org chart. Hierarchical teams with members and resource ownership.

**4. Layout**
- **Team Tree:** Hierarchical view of teams
- **Member List:** Users in selected team with roles
- **Resource Panel:** Packs, models, cases owned by team
- **Actions:** Create, Edit, Merge, Archive

**5. Key Interactions**
- Click team to view members and resources
- Drag users between teams
- Create subteam from parent
- Set team-scoped permissions

**6. State Transitions**
- Create → Configure → Active
- Merge → Select target → Confirm → Consolidated
- Archive → Confirm → Read-only

**7. Data + Agent Behavior**
- Identity and resource services
- Agents suggest team structure based on collaboration patterns
- Data: team hierarchy, memberships, resource ownership

**8. Output / Next Step**
- Team membership affects navigation and access
- Archived teams retain historical data
- Export org structure

---

### API Keys **[admin]**

**1. Context**
Management of programmatic access credentials for external integrations.

**2. Objective**
Issue, rotate, and revoke API keys with proper scoping and monitoring.

**3. Mental Model**
A credential vault. Keys, scopes, usage stats, expiration dates.

**4. Layout**
- **Key List:** Name, owner, scopes, created, expires, last used
- **Create Wizard:** Name, scopes, expiration, rate limits
- **Usage Chart:** Calls over time by key
- **Revoke Panel:** Deactivate with replacement guidance

**5. Key Interactions**
- Create opens scope selection wizard
- Click key to view usage and rotate
- Revoke requires confirmation and replacement plan
- Copy key button (visible once at creation)

**6. State Transitions**
- Create → Active → Expiring → Expired | Revoked
- Rotate → New key created → Old key deprecated

**7. Data + Agent Behavior**
- Identity service key management
- Agents detect unused keys and suggest revocation
- Data: keys, scopes, usage logs, expiration dates

**8. Output / Next Step**
- Copy key for integration configuration
- Revoke terminates API access immediately
- Export usage reports

**9. Edge Cases**
- Key leak: Emergency revoke with audit log
- High usage: Rate limit notification
- Expiration: Advance warning with renewal flow

---

## System **[admin]**

**1. Context**
Platform administration section for tenant-wide settings, audit, and health monitoring.

**2. Objective**
Configure platform behavior, monitor system health, and maintain operational integrity.

**3. Mental Model**
A system preferences and diagnostic panel. Settings, logs, health indicators.

**4. Layout**
- **Sub-navigation:** Platform Settings | Audit Log | Health Monitor
- **Dashboard:** System status, recent alerts, configuration summary
- **Content Zone:** Selected system management view

---

### Platform Settings **[admin]**

**1. Context**
Tenant-wide configuration for branding, defaults, and feature flags.

**2. Objective**
Customize platform appearance and behavior for organizational needs.

**3. Mental Model**
A settings panel. Categories, options, toggles, save/reset.

**4. Layout**
- **Category Nav:** General | Branding | Notifications | Integrations | Advanced
- **Settings Form:** Options with help text and validation
- **Preview Panel:** Live preview of branding changes
- **Actions:** Save, Reset to Defaults, Export Config

**5. Key Interactions**
- Select category to view related settings
- Edit values with inline validation
- Preview shows impact of changes
- Save applies to all tenant users

**6. State Transitions**
- Edit → Modified → Save → Applied | Validation Error
- Reset → Confirm → Default values restored

**7. Data + Agent Behavior**
- Configuration service from Layer 4
- Data: settings, branding assets, feature flags

**8. Output / Next Step**
- Settings apply tenant-wide
- Export for environment replication
- Schedule change for maintenance window

---

### Audit Log **[admin]**

**1. Context**
Comprehensive system audit trail capturing all administrative actions.

**2. Objective**
Maintain immutable record of who changed what configuration when.

**3. Mental Model**
Same as Full Change Log but scoped to administrative actions with higher detail.

**4. Layout**
- **Event Table:** Timestamp, actor, action, target, before/after summary
- **Filter Bar:** Actor, action type, target type, date range
- **Detail Drawer:** Full change payload and IP/browser context
- **Export:** CSV/JSON for compliance

**5. Key Interactions**
- Filter to find specific events
- Export for external SIEM/compliance
- Create alert rule from pattern

**6. State Transitions**
- Filter → Table refresh
- Click → Detail with full context

**7. Data + Agent Behavior**
- Audit service from shared/audit
- Agents detect suspicious patterns and alert
- Data: audit events, actor context, payloads

**8. Output / Next Step**
- Export for compliance officer
- Trigger incident from anomaly
- Configure automated alerting

---

### Health Monitor **[admin]**

**1. Context**
Operational dashboard showing system health, component status, and diagnostic information.

**2. Objective**
Proactive monitoring of platform components with alerting and troubleshooting tools.

**3. Mental Model**
A hospital monitor. Vital signs, alarms, diagnostic readouts.

**4. Layout**
- **Status Overview:** All layers with health indicators (green/yellow/red)
- **Component Grid:** Individual services with latency, errors, throughput
- **Alert Panel:** Active alerts with severity and acknowledgment
- **Diagnostic Tools:** Log search, trace lookup, test endpoints

**5. Key Interactions**
- Click component for detailed metrics
- Acknowledge alerts to silence notifications
- Diagnostic tools open in drawer
- Drill down to traces and logs

**6. State Transitions**
- Healthy → Degraded → Unhealthy → Recovering → Healthy
- Alert → Acknowledged → Resolved

**7. Data + Agent Behavior**
- Health service from Layer 4
- Agents correlate alerts and suggest root causes
- Data: health checks, metrics, alerts, traces

**8. Output / Next Step**
- Navigate to specific component logs
- Create incident from alert
- Export health report for support

**9. Edge Cases**
- Cascading failures: Show dependency map
- Metric gaps: Indicate stale data
- Alert flood: Auto-group related alerts

---

# Navigation Reference

## Quick Tier Guide

| Tier | User Types | Access Mode |
|------|------------|-------------|
| **standard** | Business users, executives | Always visible |
| **advanced** | Analysts, value engineers | Toggle-enabled for standard, always on for analysts+ |
| **admin** | Tenant admins, governance officers | Role-based access only |

## Route Patterns

| Section | Base Route | Tier |
|---------|-----------|------|
| Home | `/` | standard |
| Library | `/library/*` | standard |
| Discover | `/discover/*` | mixed |
| Model | `/model/*` | advanced |
| Deliver | `/deliver/*` | mixed |
| Evidence | `/evidence/*` | mixed |
| Govern | `/admin/*` | admin |

## Related Documentation

- [Three-Tier UX Model](../specs/three_tier_ux_model.md) — Detailed tier specification
- [API Reference](./API_REFERENCE.md) — Backend endpoints
- [Architecture Overview](./architecture_overview.md) — System design
