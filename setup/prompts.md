Here are 4 comprehensive prompts, one per layer — build them sequentially or in parallel by different teams:

---

## **LAYER 1: INTELLIGENT DATA INGESTION SERVICE**

``
Build a production-grade web data ingestion service that continuously acquires unstructured enterprise data from public sources and converts it to clean, structured Markdown ready for semantic processing.

### CORE REQUIREMENTS

**Technology Stack:**
- Python 3.11+ with asyncio
- Playwright (async) for browser automation
- Celery + Redis for distributed task queue
- PostgreSQL for crawl state and metadata persistence
- MinIO or S3 for raw content storage

**Service Architecture:**
Implement 3 microservices:
1. **Scheduler Service**: Determines what to crawl, manages priorities
2. **Crawler Workers**: Headless browser instances that execute extraction
3. **Post-Processor**: Cleans, deduplicates, and normalizes raw content

### DATA SOURCES TO SUPPORT

**Priority 1 (Enterprise Focus):**
- Corporate websites: product pages, solutions, pricing, about us, press releases
- SEC EDGAR filings: 10-K, 10-Q, 8-K (use sec-api.io or EDGAR Index files)
- Earnings call transcripts: scrape from Seeking Alpha, FactSet, or similar

**Priority 2 (Competitive Intelligence):**
- Competitor documentation sites and API references
- Industry analyst reports (public abstracts)
- Patent filings (USPTO, Google Patents)

**Priority 3 (Social/News):**
- LinkedIn company pages (public)
- News mentions via NewsAPI or GDELT

### EXTRACTION CAPABILITIES

**For each URL, extract:**
- Clean Markdown content (strip navigation, ads, footers)
- Page metadata: title, description, publish date, author
- Structured data: JSON-LD, Open Graph, Schema.org
- Links: internal (same domain) and external with anchor text
- Document type classification: product_page, press_release, financial_filing, blog_post, documentation

**Content Cleaning Pipeline:**
1. Remove boilerplate (headers, footers, sidebars) using DOM heuristics
2. Extract main content area (largest text block or article tag)
3. Convert tables to Markdown format
4. Preserve code blocks with language tags
5. Handle pagination: auto-discover and follow "next" links

### COMPLIANCE & ETHICS (NON-NEGOTIABLE)

**robots.txt Compliance:**
- Parse and cache robots.txt for 24 hours
- Respect User-agent: * and User-agent: ValueFabricBot
- Obey Crawl-delay directives
- Never crawl Disallow paths

**Rate Limiting:**
- Global: 1000 requests/minute across all workers
- Per-domain: 1 request/second with 20% jitter (0.8-1.2s)
- Per-IP rotation: Use proxy pool (BrightData, Oxylabs, or internal)
- Exponential backoff on 429/503 responses (max 5 retries)

**PII Protection:**
- Scan all extracted content with Microsoft Presidio
- Redact detected: SSN, credit cards, phone numbers, email addresses
- Block pages containing >3 PII entities (likely personal profiles)
- Log all redactions with hash of original content (not content itself)

**Legal Boundaries:**
- Only crawl publicly accessible content (no login bypass)
- Honor noindex meta tags
- Respect X-Robots-Tag HTTP headers
- Maintain audit log: URL, timestamp, IP used, bytes downloaded, outcome

### API ENDPOINTS

`
POST /crawl/website
Body: { "domain": "example.com", "depth": 2, "priority": "high" }
Response: { "job_id": "uuid", "estimated_pages": 150 }

GET /crawl/status/{job_id}
Response: { "status": "running|completed|failed", "pages_crawled": 45, "pages_total": 150 }

POST /crawl/sec-filings
Body: { "ticker": "AAPL", "form_types": ["10-K", "10-Q"], "years": 3 }

GET /content/{content_id}
Response: { "markdown": "...", "metadata": {}, "source_url": "...", "crawled_at": "..." }

DELETE /content/{content_id}
Soft delete with 30-day retention for compliance
`

### DATA MODEL (PostgreSQL)

`sql
CREATE TABLE crawl_jobs (
    id UUID PRIMARY KEY,
    domain VARCHAR(255),
    status VARCHAR(50),
    priority VARCHAR(20),
    depth INT,
    pages_crawled INT DEFAULT 0,
    pages_total INT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE crawled_content (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES crawl_jobs(id),
    url TEXT UNIQUE,
    domain VARCHAR(255),
    content_type VARCHAR(50),
    title TEXT,
    markdown_content TEXT,
    raw_html_size_bytes INT,
    markdown_size_bytes INT,
    s3_path TEXT,
    extracted_at TIMESTAMP,
    last_checked_at TIMESTAMP,
    http_status INT,
    robots_allowed BOOLEAN,
    pii_detected BOOLEAN,
    pii_entities JSONB
);

CREATE TABLE crawl_queue (
    id UUID PRIMARY KEY,
    job_id UUID,
    url TEXT,
    depth INT,
    priority INT,
    status VARCHAR(50),
    retry_count INT DEFAULT 0,
    next_retry_at TIMESTAMP
);
`

### DELIVERABLES

1. Docker Compose for local development (Redis + PostgreSQL + Crawler)
2. Kubernetes deployment manifests with HPA for crawler workers
3. Terraform for AWS infrastructure (EKS, RDS, S3)
4. Comprehensive test suite: unit tests (pytest), integration tests, load tests (Locust)
5. Monitoring: Prometheus metrics + Grafana dashboards
6. Documentation: API spec (OpenAPI), runbook, compliance audit checklist

### ACCEPTANCE CRITERIA

- [ ] Successfully crawl 1000+ pages/day without manual intervention
- [ ] Zero robots.txt violations detected by external audit
- [ ] PII detection accuracy >95% (tested on labeled dataset)
- [ ] Markdown output quality: human-rated 4+ / 5 on readability
- [ ] 99.5% uptime for API endpoints
- [ ] Handle JavaScript-rendered sites (React/Next.js/Vue) correctly
`

---

## **LAYER 2: ONTOLOGY-GUIDED EXTRACTION PIPELINE**

`
Build a semantic extraction pipeline that transforms unstructured Markdown into validated RDF/OWL triples governed by a strict enterprise ontology.

### CORE ONTOLOGY DEFINITION

Define 4 core entity types using Pydantic v2 models:

`python
class Capability(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str  # e.g., "Real-Time Data Ingestion"
    description: str
    technical_features: List[str]
    api_endpoints: List[str] = []
    integrations: List[str] = []
    apqc_mapping: Optional[str]  # APQC PCF code
    source_refs: List[str]  # URLs where mentioned
    
class UseCase(BaseModel):
    id: str
    name: str  # e.g., "Touchless Accounts Payable"
    description: str
    industry_context: List[str]  # ["Finance", "Manufacturing"]
    required_capabilities: List[str]  # Capability IDs
    workflow_steps: List[str]
    kpis: List[str]
    
class Persona(BaseModel):
    id: str
    role_type: Literal["economic_buyer", "operational_user", "stakeholder"]
    title: str  # e.g., "Chief Financial Officer"
    department: str
    pain_points: List[str]
    success_metrics: List[str]
    influenced_by: List[str] = []  # Other persona IDs
    
class ValueDriver(BaseModel):
    id: str
    category: Literal["revenue", "cost", "risk", "capital"]
    name: str  # e.g., "Operational Cost Reduction"
    description: str
    metrics: List[str]
    formula_string: Optional[str]  # e.g., "({hours_saved} * {hourly_rate}) - {implementation_cost}"
    unit: str  # e.g., "USD", "percentage"
    time_to_value: Optional[str]  # e.g., "3-6 months"
`

Define relationship types as a separate schema:

`python
class Relationship(BaseModel):
    source_id: str
    predicate: Literal[
        "enables",           # Capability → UseCase
        "requires",          # UseCase → Capability  
        "benefits",          # UseCase → Persona
        "drives",            # Persona → ValueDriver
        "contributes_to",    # Capability → ValueDriver
        "depends_on",        # Capability → Capability
        "alternative_to"     # Capability → Capability
    ]
    target_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_text: str  # Quote from source supporting this relationship
    source_url: str
`

### EXTRACTION PIPELINE ARCHITECTURE

**Stage 1: Chunking & Preprocessing**
- Input: Markdown from Layer 1
- Semantic chunking using LangChain's RecursiveCharacterTextSplitter
- Chunk size: 2000 tokens, overlap: 200 tokens
- Preserve paragraph boundaries and section headers
- Tag chunks with metadata: source URL, section type (product, pricing, case_study)

**Stage 2: Entity Extraction (LLM Call 1)**
- Model: GPT-4o or Claude 3.5 Sonnet
- Temperature: 0.0 (deterministic)
- Use function calling / tool use with strict schema
- Prompt structure:
  `
  You are an enterprise ontology extractor. Given the text below, extract all 
  entities matching the provided schema. Only extract entities you are highly 
  confident about (confidence >= 0.8). Include evidence quotes.
  
  ONTOLOGY SCHEMA: {json_schema}
  
  TEXT: {chunk}
  
  Return valid JSON matching the schema exactly.
  `

**Stage 3: Relationship Extraction (LLM Call 2)**
- Input: Extracted entities from Stage 2
- Task: Identify relationships between co-occurring entities
- Constraints: Only create relationships if explicit evidence exists in text
- Confidence threshold: 0.75

**Stage 4: Semantic Alignment & Deduplication**
- Generate embeddings for each entity name + description (text-embedding-3-large)
- Compute pairwise similarity matrix
- Merge clusters where similarity > 0.85:
  - Keep entity with most source references as canonical
  - Merge relationships to point to canonical
  - Store merged IDs as aliases
- Use Entailment LLM to validate subclass relationships:
  - "Is X a type of Y?" → yes/no/unknown

**Stage 5: Validation & Normalization**
- Schema validation using Pydantic
- Check for required fields, valid enum values
- Resolve all ID references (no dangling relationships)
- Normalize text: lowercase names for matching, preserve original in display_name

**Stage 6: RDF/OWL Serialization**
- Convert to Turtle format:
  `
  @prefix vf: <http://valuefabric.io/ontology#> .
  @prefix prov: <http://www.w3.org/ns/prov#> .
  
  vf:cap_123 a vf:Capability ;
      vf:name "Real-Time Data Ingestion" ;
      vf:description "..." ;
      vf:apqcMapping "4.1.1" ;
      prov:wasGeneratedBy vf:extraction_job_456 ;
      prov:used <https://example.com/product> .
  
  vf:cap_123 vf:enables vf:uc_789 .
  `
- Include OWL axioms for transitive properties
- Add PROV-O provenance metadata

### INDUSTRY STANDARD INTEGRATION

**APQC PCF Mapping:**
- Download APQC PCF v7.4 JSON
- Create embedding index of all process elements
- For each extracted Capability, find best matching PCF code (similarity > 0.8)
- Store mapping as skos:closeMatch or skos:exactMatch

**Financial Services (optional):**
- Integrate BIAN Service Landscape v11.0
- Map to FIBO ontology for financial instruments
- Use existing RDF dumps if available

### API ENDPOINTS

`
POST /extract
Body: { 
    "content_id": "uuid-from-layer-1",
    "extraction_config": {
        "entity_types": ["Capability", "UseCase", "Persona", "ValueDriver"],
        "confidence_threshold": 0.75
    }
}
Response: { "extraction_job_id": "uuid", "status": "queued" }

GET /extract/status/{job_id}
Response: { 
    "status": "running|completed|failed",
    "entities_extracted": 15,
    "relationships_extracted": 23,
    "rdf_output_path": "s3://bucket/extractions/job_id.ttl"
}

POST /extract/batch
Body: { "content_ids": ["uuid1", "uuid2", ...] }
Response: { "batch_job_id": "uuid" }

GET /ontology/entities
Query: ?type=Capability&limit=100
Response: { "entities": [...], "total": 1543 }

GET /ontology/relationships/{entity_id}
Response: { "incoming": [...], "outgoing": [...] }
`

### TECHNICAL REQUIREMENTS

- Async processing using Celery workers
- Rate limit LLM calls: 1000/minute (respect API quotas)
- Cache embeddings in Redis (TTL: 7 days)
- Store raw LLM responses for 30 days (audit trail)
- Implement circuit breaker for LLM failures (fallback to local model)

### DELIVERABLES

1. Pydantic models for ontology (versioned)
2. Celery tasks for each pipeline stage
3. RDF/OWL serialization library (rdflib)
4. Deduplication service with embedding cache
5. API server (FastAPI) with async endpoints
6. Integration tests with sample documents
7. Ontology visualization tool (network graph export)

### ACCEPTANCE CRITERIA

- [ ] Schema compliance: >95% of outputs pass Pydantic validation
- [ ] No hallucinated entity types (0 tolerance)
- [ ] Deduplication accuracy: >90% (measured vs human labels)
- [ ] Relationship precision: >85% (evidence-supported)
- [ ] Throughput: 100 documents/hour per worker
- [ ] RDF output validates with Apache Jena
`

---

## **LAYER 3: KNOWLEDGE GRAPH & SEMANTIC LAYER**

`
Build a production-grade Knowledge Graph with GraphRAG capabilities, semantic governance, and hybrid vector+graph retrieval.

### TECHNOLOGY STACK

**Primary Database:**
- Neo4j 5.x Enterprise Edition ( AuraDB or self-managed cluster )
- 3 core nodes (write + read) + 2 read replicas
- GDS (Graph Data Science) library for algorithms

**Vector Store:**
- Pinecone (serverless) or Weaviate
- 1536 dimensions (OpenAI embeddings)
- Metadata filtering by entity type

**API Layer:**
- FastAPI with async Neo4j driver (neo4j-python-driver)
- Cypher query builder with parameterization (prevent injection)

### DATA MODEL (Neo4j Property Graph)

`cypher
// Entity Nodes
CREATE (c:Capability {
    id: 'cap_123',
    name: 'Real-Time Data Ingestion',
    description: '...',
    embedding: [...],  // 1536-dim vector
    apqc_code: '4.1.1',
    source_url: 'https://...',
    extracted_at: datetime(),
    confidence: 0.92,
    created_by: 'extraction_job_456'
})

CREATE (u:UseCase {
    id: 'uc_789',
    name: 'Touchless AP Processing',
    industry: ['Finance', 'Healthcare'],
    embedding: [...]
})

CREATE (p:Persona {
    id: 'per_321',
    title: 'Chief Financial Officer',
    role_type: 'economic_buyer',
    department: 'Finance'
})

CREATE (v:ValueDriver {
    id: 'vd_654',
    category: 'cost',
    name: 'Operational Cost Reduction',
    formula_string: '({hours_saved} * {hourly_rate}) - {implementation_cost}',
    unit: 'USD'
})

// Relationships with properties
CREATE (c)-[:ENABLES {
    strength: 0.88,
    evidence_text: 'Real-time ingestion eliminates batch delays...',
    source_url: 'https://...'
}]->(u)

CREATE (u)-[:BENEFITS {
    impact_level: 'high',
    time_to_value: '3-6 months'
}]->(p)

CREATE (p)-[:DRIVES {
    quantified: true,
    typical_savings: 500000
}]->(v)

CREATE (c)-[:CONTRIBUTES_TO {
    weight: 0.75,
    calculation_method: 'direct'
}]->(v)
`

### SEMANTIC LAYER IMPLEMENTATION

**Centralized Metric Definitions:**
Store in PostgreSQL or as nodes in graph:

`yaml
metrics:
  arr:
    name: "Annual Recurring Revenue"
    formula: "SUM(monthly_recurring_revenue * 12)"
    unit: "USD"
    refresh_frequency: "daily"
    owner: "finance_team"
    
  nrr:
    name: "Net Revenue Retention"
    formula: "((starting_arr + expansion - contraction - churn) / starting_arr) * 100"
    unit: "percentage"
    dependencies: ["arr", "expansion_revenue", "contraction", "churn"]
``

**Access Control:**
- Row-level security: Filter by account_id or tenant_id property on nodes
- Column-level masking: Hide formula_string for non-admin users
- Relationship visibility: Some relationships marked internal: true 

**Query Interface:**
``python
class SemanticQueryEngine:
    def query_metric(self, metric_name: str, filters: dict) -> float:
        # Resolve formula from semantic layer
        # Execute against graph or warehouse
        pass
    
    def traverse_value_tree(self, capability_id: str, depth: int = 3) -> dict:
        # Cypher query for multi-hop traversal
        pass
`

### GRAPHRAG IMPLEMENTATION

**Indexing Phase (Run once, update incrementally):**
1. **Entity Embedding**: Store vector on each node (Pinecone or Neo4j vector index)
2. **Community Detection**: Run Leiden algorithm on full graph
   `
   CALL gds.leiden.stream('myGraph')
   YIELD nodeId, communityId
   `
3. **Community Summarization**: Use LLM to generate summary for each community
4. **Hierarchical Index**: Build tree of community summaries

**Retrieval Phase (Per Query):**
`python
async def graphrag_retrieve(query: str, k: int = 10) -> dict:
    # Step 1: Vector search for entry points
    query_embedding = await embed(query)
    entry_nodes = await vector_search(query_embedding, top_k=5)
    
    # Step 2: Graph traversal from entry points
    subgraphs = []
    for node in entry_nodes:
        cypher = """
        MATCH path = (start {id: $node_id})-[:ENABLES|BENEFITS|DRIVES|CONTRIBUTES_TO*1..3]-(related)
        RETURN path, relationships(path) as rels, nodes(path) as nodes
        LIMIT $limit
        """
        result = await neo4j.run(cypher, node_id=node.id, limit=k)
        subgraphs.append(result)
    
    # Step 3: Rerank by relevance to query
    scored = await rerank_subgraphs(subgraphs, query)
    
    # Step 4: Return top-k as context
    return {
        "context": format_for_llm(scored[:k]),
        "sources": extract_sources(scored[:k]),
        "citation_graph": build_citation_map(scored[:k])
    }
`

**Global Queries (Broad Questions):**
For questions like "What are our main value propositions?":
- Use community summaries as context (Map-Reduce pattern)
- No vector search needed
- Aggregate across all top-level communities

### API ENDPOINTS

`
POST /query/natural-language
Body: { "query": "How does predictive maintenance reduce costs?" }
Response: {
    "answer": "...",
    "citations": [
        {"node_id": "cap_123", "source_url": "...", "evidence": "..."}
    ],
    "confidence": 0.89
}

POST /query/traverse
Body: { 
    "start_node": "cap_123",
    "relationship_types": ["ENABLES", "BENEFITS"],
    "depth": 2
}
Response: { "subgraph": {...}, "paths": [...] }

POST /query/value-tree
Body: { "capability_id": "cap_123" }
Response: {
    "capability": {...},
    "use_cases": [...],
    "personas": [...],
    "value_drivers": [...],
    "total_roi_potential": 2500000
}

GET /semantic/metrics
Response: { "metrics": ["arr", "nrr", "cac", "ltv", ...] }

POST /semantic/calculate
Body: { 
    "metric": "roi",
    "variables": {
        "hours_saved": 5000,
        "hourly_rate": 75,
        "implementation_cost": 150000
    }
}
Response: { "result": 225000, "formula_used": "..." }
`

### PERFORMANCE REQUIREMENTS

- Single-hop query: <50ms p95
- Multi-hop (3 levels): <200ms p95
- Vector search + graph traversal: <500ms p95
- Concurrent connections: 1000+
- Graph size target: 10M nodes, 100M relationships

### DELIVERABLES

1. Neo4j schema and constraint definitions
2. Data ingestion pipeline from Layer 2 RDF → Neo4j
3. GraphRAG retrieval engine with caching
4. Semantic layer configuration (YAML + validation)
5. FastAPI application with all endpoints
6. Cypher query library (parameterized, tested)
7. Monitoring: Query performance, cache hit rates, graph growth

### ACCEPTANCE CRITERIA

- [ ] Multi-hop reasoning accuracy >90% (vs 60% vector-only baseline)
- [ ] Query latency targets met under load
- [ ] Zero Cypher injection vulnerabilities (pen tested)
- [ ] Semantic consistency: Same metric returns same value across all queries
- [ ] Community detection produces meaningful business groupings
- [ ] Full provenance: Every answer traceable to source documents
`

---

## **LAYER 4: AGENTIC WORKFLOW ENGINE**

``
Build an autonomous agent system using LangGraph that executes revenue-generating workflows on top of the Value Fabric Knowledge Graph.

### TECHNOLOGY STACK

- **Orchestration**: LangGraph (stateful multi-agent workflows)
- **LLM**: GPT-4o / Claude 3.5 Sonnet with function calling
- **State Management**: Redis for conversation persistence
- **Task Queue**: Celery for long-running workflows
- **Document Generation**: Python-docx, python-pptx, WeasyPrint (HTML→PDF)

### WORKFLOW 1: WHITESPACE ANALYSIS AGENT

**Purpose:** Autonomously research a prospect and identify expansion opportunities.

**Input:** { "prospect_domain": "targetcompany.com", "prospect_ticker": "TGT" } 

**Agent State Graph:**
``
START → [IngestProspect] → [ExtractInsights] → [MapToCapabilities] → [IdentifyWhitespace] → [GeneratePlan] → END
`

**Node Implementations:**

1. **IngestProspect**
   - Trigger Layer 1 crawl for prospect website
   - Fetch latest 10-K from SEC EDGAR
   - Wait for ingestion completion (async callback)

2. **ExtractInsights**
   - Run Layer 2 extraction on all prospect content
   - Identify: stated challenges, strategic goals, tech stack mentions
   - Store in temporary graph namespace (prospect-specific)

3. **MapToCapabilities**
   - Query Knowledge Graph: "Which of OUR capabilities solve THEIR challenges?"
   - Vector similarity search for challenge → capability matching
   - Score each match: relevance × confidence × strategic fit

4. **IdentifyWhitespace**
   - Compare prospect's current state (from scraped data) vs. required capabilities
   - Flag gaps as "whitespace opportunities"
   - Prioritize by: deal size potential, competitive positioning, time to value

5. **GeneratePlan**
   - Compile account plan with:
     - Executive summary (1 paragraph)
     - 3-5 whitespace opportunities with business case previews
     - Recommended entry points (which use case to lead with)
     - Stakeholder map (which personas to target)
   - Output: JSON + Markdown summary

**Output Schema:**
`json
{
    "prospect": "Target Company Inc.",
    "analysis_date": "2024-01-15",
    "whitespace_opportunities": [
        {
            "priority": 1,
            "capability_gap": "Real-Time Analytics",
            "business_impact": "$2.5M annual savings",
            "recommended_use_case": "Predictive Maintenance",
            "target_personas": ["VP Operations", "Plant Manager"],
            "entry_strategy": "Start with pilot at flagship facility"
        }
    ],
    "account_plan_url": "s3://.../plans/targetcompany_plan.md"
}
``

### WORKFLOW 2: DYNAMIC ROI CALCULATOR

**Purpose:** Generate defensible ROI projections using graph-stored formulas.

**Input:** { "opportunity_id": "opp_123", "prospect_metrics": {...} } 

**Implementation:**
``python
class ROICalculatorAgent:
    def __init__(self, knowledge_graph):
        self.kg = knowledge_graph
    
    async def calculate(self, capability_ids: List[str], metrics: dict) -> dict:
        # Fetch value drivers for these capabilities
        value_drivers = await self.kg.get_value_drivers(capability_ids)
        
        results = []
        for vd in value_drivers:
            # Get formula from graph
            formula = vd['formula_string']  # e.g., "({hours} * {rate}) - {cost}"
            
            # Validate all variables present
            variables = extract_variables(formula)
            missing = [v for v in variables if v not in metrics]
            
            if missing:
                results.append({
                    "value_driver": vd['name'],
                    "status": "insufficient_data",
                    "missing_variables": missing
                })
                continue
            
            # Safe evaluation
            try:
                result = safe_eval(formula, metrics)
                results.append({
                    "value_driver": vd['name'],
                    "status": "calculated",
                    "projected_value": result,
                    "unit": vd['unit'],
                    "confidence": vd.get('confidence', 0.8)
                })
            except Exception as e:
                results.append({
                    "value_driver": vd['name'],
                    "status": "error",
                    "error": str(e)
                })
        
        # Aggregate totals by category
        summary = self.aggregate_by_category(results)
        
        return {
            "detailed_results": results,
            "summary": summary,
            "total_projected_roi": sum(r['projected_value'] for r in results if r['status'] == 'calculated')
        }
    
    def safe_eval(self, formula: str, variables: dict) -> float:
        # Use numexpr or restricted Python eval
        # Whitelist: +, -, *, /, **, (), numbers, variable names
        # Blacklist: all other tokens
        pass
``

**Sensitivity Analysis:**
- Run Monte Carlo simulation with variable distributions
- Output: best case (p90), expected (p50), worst case (p10)

### WORKFLOW 3: BUSINESS CASE GENERATOR

**Purpose:** Produce consultant-grade business case documents.

**Input:** ROI calculation results, prospect context, selected capabilities

**Document Structure (auto-generated):**
1. **Executive Summary** (1 page)
   - Investment thesis in 3 bullets
   - Total projected ROI with payback period
   
2. **Current State Assessment** (1-2 pages)
   - Prospect's challenges (from scraped data)
   - Cost of inaction

3. **Proposed Solution** (2-3 pages)
   - Capabilities mapped to use cases
   - Implementation approach

4. **Financial Analysis** (2-3 pages)
   - Detailed ROI breakdown by value driver
   - Sensitivity analysis chart
   - Risk-adjusted projections

5. **Risk Mitigation** (1 page)
   - Common implementation risks
   - Mitigation strategies from similar deployments

6. **Next Steps** (0.5 page)
   - Recommended pilot scope
   - Timeline

**Output Formats:**
- Markdown (for editing)
- DOCX (Microsoft Word)
- PDF (print-ready)
- PPTX (presentation deck, 10-15 slides)

### WORKFLOW 4: PROVENANCE AUDIT AGENT

**Purpose:** Provide full transparency into any generated output.

**Input:** { "output_id": "doc_123", "output_type": "business_case" } 

**Functionality:**
- Traverse PROV-O graph backward from output
- Show: which LLM calls → which extractions → which source documents
- Display confidence scores at each step
- Highlight any low-confidence (<0.8) links in the chain

**API Endpoint:**
``
GET /audit/trace/{output_id}
Response: {
    "output": {...},
    "provenance_chain": [
        {"step": "business_case_generation", "llm": "gpt-4o", "prompt_version": "abc123"},
        {"step": "roi_calculation", "formulas": [...], "variables": [...]},
        {"step": "value_driver_extraction", "source_nodes": [...]},
        {"step": "web_scraping", "source_urls": [...]}
    ],
    "low_confidence_links": [...],
    "source_documents": [...]
}
`

### AGENT ORCHESTRATION

**LangGraph State Definition:**
`python
class AgentState(TypedDict):
    workflow_type: str  # whitespace|roi|business_case|audit
    input_data: dict
    intermediate_results: dict
    current_step: str
    error: Optional[str]
    final_output: Optional[dict]
    human_in_the_loop: Optional[dict]  # For approvals
``

**Tool Registry (available to all agents):**
- knowledge_graph_query(cypher: str) -> dict 
- web_search(query: str) -> list 
- calculate_roi(formula: str, variables: dict) -> float 
- generate_document(template: str, data: dict) -> bytes 
- send_notification(recipient: str, message: str) -> None 

**Human-in-the-Loop:**
- Pause workflow for approval at critical points:
  - Before sending business case to prospect
  - When ROI projection exceeds $10M (flag for review)
  - When confidence score < 0.7

### API ENDPOINTS

``
POST /agents/whitespace
Body: { "prospect_domain": "...", "prospect_ticker": "..." }
Response: { "workflow_id": "uuid", "status": "started" }

POST /agents/roi
Body: { "capability_ids": [...], "prospect_metrics": {...} }
Response: { "calculation_id": "uuid", "result": {...} }

POST /agents/business-case
Body: { "opportunity_id": "...", "format": "pdf|docx|pptx" }
Response: { "document_url": "s3://...", "pages": 12 }

GET /agents/status/{workflow_id}
Response: { "status": "running|paused|completed|failed", "current_step": "..." }

POST /agents/{workflow_id}/approve
Body: { "decision": "approve|reject", "notes": "..." }
Response: { "status": "resumed|cancelled" }
`

### DELIVERABLES

1. LangGraph state machines for each workflow (Python)
2. Agent tool implementations with error handling
3. Document generation templates (Jinja2 → DOCX/PDF/PPTX)
4. Human-in-the-loop UI components (or webhook integrations)
5. Workflow monitoring dashboard (step latency, success rates)
6. Conversation history API (audit trail)

### ACCEPTANCE CRITERIA

- [ ] Whitespace analysis completes end-to-end in <5 minutes
- [ ] ROI calculations are deterministic (same inputs → same outputs)
- [ ] Business case documents rated 4+ / 5 by sales team
- [ ] Full provenance trace available in <500ms
- [ ] Human-in-the-loop triggers work correctly
- [ ] 99% workflow completion rate (minimal failures)
- [ ] All agent actions logged with PROV-O metadata
``

---

These 4 prompts can be given to separate engineering teams or executed sequentially. Layer 2 depends on Layer 1's output format, Layer 3 depends on Layer 2's RDF, and Layer 4 depends on Layer 3's graph API.