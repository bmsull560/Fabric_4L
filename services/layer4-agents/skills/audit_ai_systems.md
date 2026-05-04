---
name: audit_ai_systems
description: Comprehensive audit of AI/ML systems including prompt injection detection, model governance validation, RAG architecture review, and LLM cost anomaly detection. Use when auditing agentic systems, LLM integrations, or preparing AI/ML components for production.
allowed_agents: ["security-auditor", "compliance-auditor", "ml-engineer", "pre-production-audit"]
---

# Audit AI Systems Skill

## Purpose

This skill provides systematic auditing of AI/ML components in the Value Fabric platform, with particular focus on:
- Prompt injection and security vulnerabilities in LLM interactions
- Model governance, versioning, and lifecycle management
- RAG (Retrieval-Augmented Generation) architecture validation
- LLM cost monitoring and anomaly detection
- Agent orchestration reliability and checkpoint validation

## When to Use

- Pre-production validation of LLM-powered features (Layer 2 extraction, Layer 4 agents)
- Quarterly AI/ML security assessments
- After prompt or model configuration changes
- When investigating LLM-related security incidents
- During SOC 2/ISO 27001 audits covering AI systems
- Cost optimization reviews for LLM usage

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| audit_scope | string | No | "all" | Areas: all, prompt_security, model_governance, rag_architecture, llm_costs, agent_orchestration |
| layers | string[] | No | ["L2", "L4"] | Layers to audit (L2=extraction, L4=agents) |
| prompt_paths | string[] | No | ["value-fabric/layer2-extraction/.../prompts/"] | Paths to prompt files for scanning |
| severity_threshold | string | No | "medium" | Minimum severity: critical, high, medium, low |
| include_cost_analysis | boolean | No | true | Include LLM cost anomaly detection |
| check_model_registry | boolean | No | true | Validate model registry entries |
| output_format | string | No | "markdown" | Output: markdown, json, sarif |
| fail_on_critical | boolean | No | true | Fail if critical findings detected |

## Audit Steps

### 1. Prompt Security Analysis

Scan all prompt files for injection vulnerabilities:

```bash
# Locate all prompt files
find value-fabric/layer2-extraction -name "*.md" -o -name "*.txt" -o -name "*.prompt" | grep -i prompt

# Check for injection patterns
```

**Injection Patterns to Detect:**
- Direct user input interpolation without sanitization
- System prompt boundaries that can be escaped
- Missing input validation before LLM calls
- Prompt chaining without intermediate validation
- System instructions that can be overridden

**Example Vulnerability:**
```python
# VULNERABLE - Direct user input in prompt
prompt = f"Extract entities from: {user_input}"

# SECURE - Validated, bounded input
validated = validate_and_truncate(user_input, max_chars=1000)
prompt = f"Extract entities from: {validated}"
```

### 2. Model Governance Validation

Verify model lifecycle management:

```bash
# Check model registry entries
curl -s http://localhost:8004/v1/models | jq '.models[] | {id, version, status}'

# Verify model versioning consistency
```

**Checks:**
- [ ] All production models have registry entries
- [ ] Model versions are immutable (no silent updates)
- [ ] Fallback models configured for critical paths
- [ ] Model deprecation notices published
- [ ] Model performance benchmarks recorded

### 3. RAG Architecture Assessment

Evaluate knowledge retrieval systems:

```python
# Test retrieval accuracy
async def test_retrieval_accuracy(query: str, expected_entities: list):
    response = await hybrid_search(query)
    retrieved = [e.name for e in response.entities]
    
    precision = len(set(retrieved) & set(expected_entities)) / len(retrieved)
    recall = len(set(retrieved) & set(expected_entities)) / len(expected_entities)
    
    return {"precision": precision, "recall": recall, "f1": 2 * (precision * recall) / (precision + recall)}
```

**Metrics to Validate:**
- Query latency p99 < 500ms (Layer 3 SLO)
- Retrieval precision > 85%
- Embedding model consistency
- Vector index freshness

### 4. LLM Cost Anomaly Detection

Analyze cost patterns and detect anomalies:

```promql
# Current cost rate
sum(rate(vf_llm_cost_usd_total[1h]))

# Cost by layer
sum by (layer) (rate(vf_llm_cost_usd_total[1h]))

# Anomaly: cost > 3 standard deviations from 7-day mean
```

**Thresholds:**
- Warning: > $50/hour sustained for 15 minutes
- Critical: > $100/hour sustained for 10 minutes
- Anomaly: > 3σ from 7-day rolling average

### 5. Agent Orchestration Review

Validate LangGraph workflow reliability:

```bash
# Check checkpoint reliability
curl -s http://localhost:8004/v1/workflows/checkpoint-stats | jq

# Verify failure recovery rates
```

**Checks:**
- Checkpoint success rate > 99.9%
- Workflow resume success rate > 95%
- State serialization completeness
- Timeout handling correctness

## Output Structure

### Summary
- Total findings by severity
- Audit scope and layers covered
- Overall AI/ML security posture score

### Findings Categories

**Prompt Security Findings:**
```json
{
  "file": "value-fabric/layer2-extraction/.../extraction.prompt",
  "line": 42,
  "severity": "high",
  "category": "unsanitized_input",
  "description": "User input directly interpolated into prompt",
  "remediation": "Add input validation and length limits before interpolation",
  "pattern_detected": "{user_content}"
}
```

**Model Governance Findings:**
```json
{
  "model_id": "gpt-4-extraction",
  "severity": "medium",
  "issue": "No fallback model configured for critical extraction path",
  "recommendation": "Configure gpt-3.5-turbo as fallback with degraded mode"
}
```

**RAG Architecture Findings:**
```json
{
  "component": "hybrid_search",
  "severity": "warning",
  "metric": "p99_latency",
  "current_value": 750,
  "threshold": 500,
  "recommendation": "Add query result caching for common patterns"
}
```

## Safety Notes

- **Critical findings block production deployment** - All critical severity issues must be resolved
- Prompt security vulnerabilities can lead to data exfiltration or system compromise
- Model drift can cause silent degradation in extraction quality
- Always validate in staging environment before production audit

## Example Usage

```bash
# Full AI/ML audit
python -m layer4_agents.tools.audit_ai_systems --scope all --layers L2,L4

# Prompt security only
python -m layer4_agents.tools.audit_ai_systems --scope prompt_security --severity-threshold high

# Cost analysis with anomaly detection
python -m layer4_agents.tools.audit_ai_systems --scope llm_costs --include-cost-analysis

# CI gate mode (fails on critical)
python -m layer4_agents.tools.audit_ai_systems --fail-on-critical --output-format json
```

## Integration with Pre-Production Audit

This skill is automatically invoked by the `pre-production-audit` workflow when:
- Layer 2 or Layer 4 changes are detected
- Prompt files are modified
- Model configurations are updated
- LLM cost alerts have fired in the past 7 days

## Related Skills

- `assess_drift` - Detect configuration drift in AI/ML components
- `audit_compliance` - Validate AI/ML compliance (SOC 2, GDPR)
- `evaluate_formula` - Test formula evaluation with LLM components
