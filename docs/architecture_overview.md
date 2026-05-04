# Value Fabric - Architectural Design Overview

## System Architecture

Value Fabric employs a **6-layer pipeline architecture** that progressively transforms raw data into actionable business intelligence:

```
┌─────────────────────────────────────────────────────────────┐
│                     LAYER 6: BENCHMARKS                     │
│         (Peer Comparison, Statistical Validation)           │
├─────────────────────────────────────────────────────────────┤
│                   LAYER 5: GROUND TRUTH                     │
│     (TruthObject Validation, Maturity Ladder, Evidence)     │
├─────────────────────────────────────────────────────────────┤
│                     LAYER 4: AGENTS                         │
│         (AI Skills, Workflows, Business Logic)              │
├─────────────────────────────────────────────────────────────┤
│                   LAYER 3: KNOWLEDGE                        │
│       (Knowledge Graph, Embeddings, Query Engine)           │
├─────────────────────────────────────────────────────────────┤
│                  LAYER 2: EXTRACTION                        │
│     (Entity Extraction, Relationship Mapping, NLP)          │
├─────────────────────────────────────────────────────────────┤
│                   LAYER 1: INGESTION                        │
│    (Document Processing, OCR, Chunking, Vectorization)      │
└─────────────────────────────────────────────────────────────┘
```

## Layer 1: Ingestion

**Purpose**: Convert unstructured source materials into processable content units

### Components
- **Document Processor**: PDF, DOCX, HTML parsing with OCR fallback
- **Chunking Engine**: Semantic and fixed-size chunking strategies
- **Vector Store**: Embeddings for semantic search and retrieval
- **Source Registry**: Document metadata, freshness tracking, access URLs

### Key Design Decisions
- Chunk boundaries respect semantic structure (headings, paragraphs)
- Source documents are immutable; updates create new versions
- Each chunk maintains provenance link to parent document

## Layer 2: Extraction

**Purpose**: Identify entities and relationships from ingested content

### Components
- **Entity Extractor**: LLM-based extraction of typed entities (Capability, UseCase, Persona, ValueDriver)
- **Relationship Mapper**: Identifies connections (ENABLES, BENEFITS, DRIVES, CONTRIBUTES_TO)
- **Evidence Linker**: Associates claims with source text spans
- **Confidence Scorer**: Assigns confidence scores to extractions

### Entity Taxonomy
```
Capability → UseCase → Persona → ValueDriver
   ↓           ↓          ↓           ↓
[What we]  [How it's] [Who]     [Business]
[do]       [used]     [benefits] [outcome]
```

### Extraction Pipeline
1. LLM extracts candidate entities from chunks
2. Deduplication via embedding similarity
3. Relationship inference from co-occurrence and explicit statements
4. Evidence quotes linked to source spans
5. Confidence scoring based on source quality and extraction clarity

## Layer 3: Knowledge

**Purpose**: Store, index, and query the knowledge graph

### Data Model

**Nodes**:
- `Capability`: Technical abilities or features
- `UseCase`: Scenarios where capabilities are applied
- `Persona`: Stakeholder roles (CFO, CIO, VP Operations)
- `ValueDriver`: Business outcomes (Cost Reduction, Risk Mitigation)
- `Formula`: Mathematical models for quantification
- `Industry`: Industry segments with benchmarks

**Relationships**:
- `ENABLES`: Capability → UseCase
- `BENEFITS`: UseCase → Persona
- `DRIVES`: UseCase → ValueDriver
- `CONTRIBUTES_TO`: ValueDriver → ValueDriver (hierarchical)
- `HAS_FORMULA`: ValueDriver → Formula
- `APPLIES_TO`: Benchmark → Industry

### Query Capabilities
- **Graph Traversal**: Navigate relationships with depth/breadth constraints
- **Semantic Search**: Embedding-based entity retrieval
- **Path Finding**: Shortest/strongest paths between entities
- **Value Tree Resolution**: Build complete value chains from any node

### Storage Strategy
- Graph database for relationships (Neo4j-compatible)
- Vector database for semantic search (pgvector)
- Relational store for metadata and audit logs

## Layer 4: Agents

**Purpose**: Execute business logic through composable skills and workflows

### Skill Architecture

Skills are atomic capabilities invoked via slash commands:

**Tier 1: Knowledge Navigation**
- `/graph_traverse` - Navigate relationships
- `/semantic_search` - Find by meaning
- `/resolve_value_tree` - Build value trees
- `/find_path` - Path between entities

**Tier 2: Reasoning**
- `/multi_hop_reason` - Complex multi-hop questions
- `/analyze_gaps` - Missing capabilities

**Tier 3: Calculation**
- `/evaluate_formula` - Execute formulas
- `/sensitivity_analysis` - Monte Carlo simulation

**Tier 4: Content Generation**
- `/build_narrative` - Create stories
- `/generate_business_case` - Full documents
- `/write_executive_summary` - Condense analysis

**Tier 5: Research**
- `/research_web` - External research
- `/analyze_competitor` - Competitive analysis
- `/enrich_industry_context` - Industry benchmarks

**Tier 6: Audit**
- `/trace_provenance` - Lineage tracking
- `/escalate_to_human` - Human escalation

**Tier 7: Meta**
- `/value_fabric_help` - Skill discovery

### Workflow Composition

Workflows orchestrate skills into business processes:

```
Whitespace Analysis:
  research_web → semantic_search → graph_traverse → analyze_gaps → generate_business_case

ROI Calculator:
  resolve_value_tree → evaluate_formula → sensitivity_analysis

Business Case Generator:
  multi_hop_reason → enrich_industry_context → build_narrative → write_executive_summary
```

## Data Flow

### Ingestion Flow
```
Source Document → Chunking → Embedding → Storage
                    ↓
              Extraction → Entity/Relation → Knowledge Graph
```

### Query Flow
```
User Query → Agent Router → Skill Selection → Graph Query/Search → Response Synthesis
                                                    ↓
                                              Confidence Check → Human Escalation (if needed)
```

### Generation Flow
```
Request → Value Tree Resolution → Formula Evaluation → Narrative Building → Document Assembly
              ↓                        ↓                      ↓
        Provenance Chain ← Evidence Quotes ← Source Documents
```

## Confidence & Provenance

### Confidence Scoring
Every entity, relationship, and generated output carries a confidence score (0.0-1.0):
- Source quality (authoritative vs. speculative)
- Extraction clarity (explicit vs. inferred)
- Evidence strength (direct quote vs. paraphrase)
- Model certainty (token probabilities)

### Provenance Chain
Full lineage from output back to source:
```
Business Case → Narrative → Value Tree → Relationships → Extractions → Chunks → Documents
```

Each link includes:
- Timestamp
- Processing version
- Confidence at that step
- Evidence quotes

## Deployment Architecture

### Container Strategy
Each layer runs as independent container:
- Layer 1: Document processing workers
- Layer 2: LLM-based extraction (GPU-enabled)
- Layer 3: API server + graph database
- Layer 4: Agent runtime
- Layer 5: Ground truth validation service
- Layer 6: Benchmark harness

### Communication
- Layer-to-layer: gRPC APIs
- Event streaming: Redis/RabbitMQ for async processing
- Storage: PostgreSQL + Neo4j + MinIO (object storage)

### Scalability
- Layer 1 & 2: Horizontal scaling via worker pools
- Layer 3: Read replicas for query load
- Layer 4: Stateless, scales with request volume

## Security Considerations

- **Data Isolation**: Customer data segmented by tenant
- **Audit Logging**: All agent decisions logged with tamper-evident hashes
- **Access Control**: Role-based permissions for knowledge graph access
- **PII Handling**: Automatic detection and redaction in source documents

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| Ingestion | Python, PyPDF, Tesseract, sentence-transformers |
| Extraction | Python, OpenAI/Anthropic APIs, spaCy, Pydantic |
| Knowledge | PostgreSQL, pgvector, Neo4j, SQLAlchemy |
| Agents | Python, FastAPI, LangGraph, Pydantic |
| Ground Truth | Python, FastAPI, PostgreSQL |
| Benchmarks | Python, FastAPI, statistical libraries |
| Infrastructure | Docker, Docker Compose, Redis |

---

*Document Version: 1.1*  
*Last Updated: May 2026*
