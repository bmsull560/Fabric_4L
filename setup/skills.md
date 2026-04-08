Here are the **core skills** every Value Fabric agent should possess — implement these as a **tool registry** for your agent framework:

---

# **VALUE FABRIC: AGENT SKILL TAXONOMY**

## **TIER 1: KNOWLEDGE NAVIGATION SKILLS**

### **1.1 Graph Traversal (`graph_traverse`)**
```python
{
  "name": "graph_traverse",
  "description": "Navigate the Knowledge Graph via relationships to find connected entities",
  "parameters": {
    "start_node_id": "string - Entity to start from",
    "relationship_types": ["ENABLES", "BENEFITS", "DRIVES", "CONTRIBUTES_TO"],
    "direction": "OUTGOING|INCOMING|BOTH",
    "depth": "integer 1-5 (default: 2)",
    "min_confidence": "float 0.0-1.0 - Filter by relationship confidence"
  },
  "returns": "Subgraph with nodes, relationships, and evidence quotes"
}
```
**Example Use:** "Find all Value Drivers reachable from Capability X"

---

### **1.2 Semantic Search (`semantic_search`)**
```python
{
  "name": "semantic_search",
  "description": "Find entities by meaning, not just keywords",
  "parameters": {
    "query": "natural language description",
    "entity_types": ["Capability", "UseCase", "Persona", "ValueDriver"],
    "top_k": "integer (default: 5)",
    "similarity_threshold": "float 0.0-1.0 (default: 0.8)"
  },
  "returns": "Ranked list of entities with similarity scores"
}
```
**Example Use:** "Find capabilities related to predictive analytics"

---

### **1.3 Value Tree Resolver (`resolve_value_tree`)**
```python
{
  "name": "resolve_value_tree",
  "description": "Build complete Value Tree from any starting node",
  "parameters": {
    "start_node_id": "string",
    "direction": "UP (to Value Drivers)|DOWN (to Capabilities)|BOTH",
    "include_formulas": "boolean - Include mathematical formulas"
  },
  "returns": "Hierarchical tree: Capabilities → Use Cases → Personas → Value Drivers"
}
```
**Example Use:** "Show me the complete value proposition for this capability"

---

### **1.4 Path Finder (`find_path`)**
```python
{
  "name": "find_path",
  "description": "Find shortest or strongest path between two entities",
  "parameters": {
    "source_id": "string",
    "target_id": "string",
    "algorithm": "SHORTEST|STRONGEST (by confidence)|ALL",
    "max_hops": "integer (default: 5)"
  },
  "returns": "List of paths with confidence scores and evidence"
}
```
**Example Use:** "How does Real-Time Ingestion contribute to Cost Reduction?"

---

## **TIER 2: REASONING & INFERENCE SKILLS**

### **2.1 Multi-Hop Reasoning (`multi_hop_reason`)**
```python
{
  "name": "multi_hop_reason",
  "description": "Answer complex questions requiring multiple graph traversals",
  "parameters": {
    "question": "natural language question",
    "max_hops": "integer (default: 3)",
    "require_evidence": "boolean - Include supporting quotes"
  },
  "returns": "Answer + reasoning chain + source citations"
}
```
**Example Use:** "Which personas benefit most from our AI capabilities in manufacturing?"

---

### **2.2 Gap Analysis (`analyze_gaps`)**
```python
{
  "name": "analyze_gaps",
  "description": "Identify missing capabilities or disconnected value chains",
  "parameters": {
    "context": "prospect description or requirements",
    "comparison_scope": "FULL_GRAPH|SUBSET (provide node_ids)",
    "gap_types": ["MISSING_CAPABILITY", "DISCONNECTED_VALUE", "UNMAPPED_PERSONA"]
  },
  "returns": "List of gaps with severity scores and recommendations"
}
```
**Example Use:** "What capabilities are we missing for healthcare prospects?"

---

### **2.3 Conflict Detection (`detect_conflicts`)**
```python
{
  "name": "detect_conflicts",
  "description": "Find contradictory information in the graph",
  "parameters": {
    "entity_id": "string - Entity to check",
    "check_types": ["DUPLICATE_NAMES", "CONTRADICTORY_RELATIONSHIPS", "FORMULA_ERRORS"]
  },
  "returns": "List of conflicts with suggested resolutions"
}
```
**Example Use:** "Are there conflicting ROI formulas for this use case?"

---

## **TIER 3: CALCULATION & QUANTIFICATION SKILLS**

### **3.1 Formula Evaluator (`evaluate_formula`)**
```python
{
  "name": "evaluate_formula",
  "description": "Execute mathematical formulas from Value Drivers with variable substitution",
  "parameters": {
    "formula_id": "string - ValueDriver node ID",
    "variables": {"var_name": numeric_value},
    "scenario": "BASE|BEST|WORST - For sensitivity analysis"
  },
  "returns": "Calculated value + intermediate steps + unit"
}
```
**Example Use:** "Calculate ROI given 5000 hours saved at $75/hour"

---

### **3.2 Sensitivity Analyzer (`sensitivity_analysis`)**
```python
{
  "name": "sensitivity_analysis",
  "description": "Run Monte Carlo simulation on formula variables",
  "parameters": {
    "formula_id": "string",
    "variable_distributions": {
      "var_name": {"distribution": "normal|uniform|triangular", "params": {...}}
    },
    "iterations": "integer (default: 1000)",
    "confidence_intervals": [0.5, 0.9]
  },
  "returns": "Distribution statistics, p10/p50/p90 values, risk assessment"
}
```
**Example Use:** "What's the range of possible ROI outcomes?"

---

### **3.3 Metric Aggregator (`aggregate_metrics`)**
```python
{
  "name": "aggregate_metrics",
  "description": "Roll up metrics across multiple entities or time periods",
  "parameters": {
    "metric_name": "string - From semantic layer",
    "entity_ids": ["list of node IDs"],
    "aggregation": "SUM|AVG|MIN|MAX|MEDIAN",
    "group_by": "optional grouping field"
  },
  "returns": "Aggregated value with breakdown"
}
```
**Example Use:** "Total addressable value across these 5 capabilities"

---

## **TIER 4: CONTENT GENERATION SKILLS**

### **4.1 Business Case Synthesizer (`generate_business_case`)**
```python
{
  "name": "generate_business_case",
  "description": "Create consultant-grade business case document",
  "parameters": {
    "opportunity_context": {"prospect": "...", "industry": "...", "challenges": [...]},
    "capability_ids": ["capabilities to include"],
    "output_format": "MARKDOWN|DOCX|PDF|PPTX",
    "sections": ["EXECUTIVE_SUMMARY", "ROI_ANALYSIS", "RISK_MITIGATION"],
    "tone": "EXECUTIVE|TECHNICAL|FINANCIAL"
  },
  "returns": "Document URL + key highlights + confidence score"
}
```
**Example Use:** "Generate a business case for Target Corp using our analytics capabilities"

---

### **4.2 Executive Summary Writer (`write_executive_summary`)**
```python
{
  "name": "write_executive_summary",
  "description": "Distill complex analysis into 1-page executive summary",
  "parameters": {
    "source_analysis": "reference to previous agent output",
    "focus": "ROI|STRATEGIC_FIT|RISK|IMPLEMENTATION",
    "max_length": "word count (default: 300)"
  },
  "returns": "Concise summary with bullet points and key numbers"
}
```

---

### **4.3 Narrative Builder (`build_narrative`)**
```python
{
  "name": "build_narrative",
  "description": "Create compelling story connecting capabilities to outcomes",
  "parameters": {
    "starting_point": "Capability or challenge description",
    "audience": "CFO|CIO|VP_Operations|Procurement",
    "story_arc": "PROBLEM_SOLUTION|TRANSFORMATION|COMPETITIVE_ADVANTAGE"
  },
  "returns": "Structured narrative with hooks, evidence, and call-to-action"
}
```
**Example Use:** "Create a story for a CFO about reducing operational costs"

---

## **TIER 5: RESEARCH & ENRICHMENT SKILLS**

### **5.1 Web Researcher (`research_web`)**
```python
{
  "name": "research_web",
  "description": "Search web for additional context not in Knowledge Graph",
  "parameters": {
    "query": "search query",
    "sources": ["NEWS", "FINANCIAL", "COMPANY_WEBSITE", "INDUSTRY_REPORTS"],
    "max_results": "integer (default: 5)",
    "recency_days": "integer - How recent should results be"
  },
  "returns": "Summarized findings with source URLs"
}
```
**Example Use:** "What are Target Corp's stated strategic priorities for 2024?"

---

### **5.2 Competitor Analyzer (`analyze_competitor`)**
```python
{
  "name": "analyze_competitor",
  "description": "Compare competitor capabilities against our Value Tree",
  "parameters": {
    "competitor_name": "string",
    "comparison_dimensions": ["CAPABILITIES", "PRICING", "POSITIONING", "CUSTOMERS"]
  },
  "returns": "Competitive positioning matrix with whitespace opportunities"
}
```

---

### **5.3 Industry Context Enricher (`enrich_industry_context`)**
```python
{
  "name": "enrich_industry_context",
  "description": "Add industry-specific benchmarks and trends to analysis",
  "parameters": {
    "industry": "string - e.g., 'Manufacturing', 'Healthcare'",
    "context_type": "BENCHMARKS|REGULATIONS|TRENDS|PAIN_POINTS"
  },
  "returns": "Relevant industry data with sources"
}
```
**Example Use:** "What are typical cost reduction benchmarks in manufacturing?"

---

## **TIER 6: AUDIT & PROVENANCE SKILLS**

### **6.1 Provenance Tracer (`trace_provenance`)**
```python
{
  "name": "trace_provenance",
  "description": "Show complete lineage of any generated output",
  "parameters": {
    "output_id": "string - ID of generated document or calculation",
    "depth": "FULL|SUMMARY - Level of detail"
  },
  "returns": "Chain of custody: LLM calls → extractions → source documents"
}
```
**Example Use:** "Where did this $2.5M ROI number come from?"

---

### **6.2 Confidence Auditor (`audit_confidence`)**
```python
{
  "name": "audit_confidence",
  "description": "Identify low-confidence links in reasoning chain",
  "parameters": {
    "analysis_id": "string",
    "confidence_threshold": "float (default: 0.8)"
  },
  "returns": "List of weak points with suggestions for improvement"
}
```

---

### **6.3 Source Verifier (`verify_sources`)**
```python
{
  "name": "verify_sources",
  "description": "Check if source documents still exist and are up-to-date",
  "parameters": {
    "entity_id": "string",
    "max_age_days": "integer - Flag sources older than this"
  },
  "returns": "Source health report with recommendations for re-crawl"
}
```

---

## **TIER 7: COLLABORATION & WORKFLOW SKILLS**

### **7.1 Human Escalator (`escalate_to_human`)**
```python
{
  "name": "escalate_to_human",
  "description": "Request human review or approval",
  "parameters": {
    "reason": "LOW_CONFIDENCE|HIGH_IMPACT|AMBIGUITY|POLICY_VIOLATION",
    "context": "explanation of what needs review",
    "urgency": "LOW|MEDIUM|HIGH|CRITICAL",
    "required_approvers": ["role or user ID"]
  },
  "returns": "Ticket ID + estimated response time"
}
```
**When to Use:**
- Confidence < 0.7 on critical claims
- ROI projection > $10M
- Conflicting information detected
- First-time use case

---

### **7.2 Clarification Seeker (`ask_clarification`)**
```python
{
  "name": "ask_clarification",
  "description": "Ask user for missing information",
  "parameters": {
    "missing_info": "description of what's needed",
    "options": ["optional", "predefined", "choices"],
    "impact": "how this affects the analysis"
  },
  "returns": "Question formatted for user"
}
```
**Example:** "What's your current customer churn rate? This affects the retention value calculation."

---

### **7.3 Workflow Planner (`plan_workflow`)**
```python
{
  "name": "plan_workflow",
  "description": "Break complex request into executable sub-tasks",
  "parameters": {
    "objective": "high-level goal",
    "constraints": ["time", "budget", "data availability"],
    "available_tools": ["list of tool names the agent can use"]
  },
  "returns": "Step-by-step execution plan with dependencies"
}
```

---

## **TIER 8: META-COGNITIVE SKILLS**

### **8.1 Self-Correction (`self_correct`)**
```python
{
  "name": "self_correct",
  "description": "Detect and fix errors in previous reasoning",
  "parameters": {
    "previous_output_id": "string",
    "error_type": "CALCULATION|LOGIC|MISSING_CONTEXT|CONTRADICTION",
    "correction_strategy": "RECALCULATE|REQUERY|RESEARCH|ESCALATE"
  },
  "returns": "Corrected output + explanation of changes"
}
```

---

### **8.2 Uncertainty Quantifier (`quantify_uncertainty`)**
```python
{
  "name": "quantify_uncertainty",
  "description": "Express confidence levels appropriately in outputs",
  "parameters": {
    "claim": "statement to evaluate",
    "evidence_strength": "STRONG|MODERATE|WEAK",
    "data_completeness": "COMPLETE|PARTIAL|INFERRED"
  },
  "returns": "Qualified statement with appropriate hedging"
}
```
**Example Output:** "Based on available data, we project $2.5M in savings (confidence: 75%, based on 3 similar deployments)"

---

### **8.3 Knowledge Gap Identifier (`identify_knowledge_gaps`)**
```python
{
  "name": "identify_knowledge_gaps",
  "description": "Recognize when graph doesn't have needed information",
  "parameters": {
    "query": "what the user is asking",
    "graph_coverage": "percentage of query concepts found in graph"
  },
  "returns": "Specific gaps + suggestions for filling them (crawl, research, ask user)"
}
```

---

## **SKILL COMPOSITION PATTERNS**

### **Common Agent Workflows**

**Whitespace Analysis Agent:**
```
research_web → semantic_search → graph_traverse → analyze_gaps → 
generate_business_case → trace_provenance → escalate_to_human (if high value)
```

**ROI Calculator Agent:**
```
resolve_value_tree → evaluate_formula → sensitivity_analysis → 
quantify_uncertainty → trace_provenance
```

**Business Case Generator:**
```
multi_hop_reason → enrich_industry_context → build_narrative → 
write_executive_summary → generate_business_case → audit_confidence
```

---

## **IMPLEMENTATION NOTES**

### **Tool Registry Structure**
```python
# tools/__init__.py
from .knowledge import graph_traverse, semantic_search, resolve_value_tree
from .reasoning import multi_hop_reason, analyze_gaps, detect_conflicts
from .calculation import evaluate_formula, sensitivity_analysis, aggregate_metrics
from .generation import generate_business_case, write_executive_summary, build_narrative
from .research import research_web, analyze_competitor, enrich_industry_context
from .audit import trace_provenance, audit_confidence, verify_sources
from .collaboration import escalate_to_human, ask_clarification, plan_workflow
from .meta import self_correct, quantify_uncertainty, identify_knowledge_gaps

TOOL_REGISTRY = {
    "graph_traverse": graph_traverse,
    "semantic_search": semantic_search,
    # ... all tools
}
```

### **Error Handling**
Every tool must return:
```python
{
  "success": bool,
  "data": {...},  # if success
  "error": {       # if not success
    "code": "TOOL_ERROR_CODE",
    "message": "human-readable",
    "suggestion": "how to proceed"
  },
  "metadata": {
    "execution_time_ms": 150,
    "confidence": 0.92,
    "sources": [...]
  }
}
```

### **Rate Limiting**
- Graph queries: 100/minute per agent
- LLM calls: 20/minute per agent (cost control)
- Web research: 10/minute per agent (respect sources)

---

These skills give your agents the full range of capabilities needed to operate effectively within the Value Fabric — from deep knowledge navigation to human-like reasoning to transparent auditability.