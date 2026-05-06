# Layer 4: Agentic Workflow Engine

LangGraph-powered agentic workflow layer for the Value Fabric platform.

## Overview

Layer 4 transforms structured knowledge into actionable business intelligence through AI agent workflows:

- **LangGraph Workflow Engine**: State-machine orchestrated agent graphs
- **ROI Calculator**: Formula-based value quantification
- **Whitespace Analysis**: Gap detection between needs and capabilities  
- **Business Case Generator**: Automated ROI-driven document generation
- **Tool Registry**: 24+ reusable skills for agents

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Set environment variables
export OPENAI_API_KEY=sk-...
export NEO4J_URI=bolt://localhost:7687
export REDIS_URL=redis://localhost:6379
export LAYER1_API_URL=https://layer1-ingestion.value-fabric.svc.cluster.local:8000
export LAYER2_API_URL=https://layer2-extraction.value-fabric.svc.cluster.local:8000
export LAYER3_API_URL=https://layer3-knowledge.value-fabric.svc.cluster.local:8001
export LAYER5_API_URL=https://layer5-ground-truth.value-fabric.svc.cluster.local:8005

# Optional: enable only when HTTPS is terminated by an enforced service mesh mTLS path
export SERVICE_MESH_MTLS_ENABLED=true

# Run tests
pytest tests/ -v

# Start API server
uvicorn src.api.main:app --reload
```

## Architecture

```
src/
├── models/          # Agent state, workflow configs, tool schemas
├── workflows/       # LangGraph workflow definitions
├── tools/           # 24 skill implementations
├── engine/          # Core workflow execution engine
└── api/             # FastAPI REST endpoints
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /v1/workflows` | Create workflow instance |
| `POST /v1/workflows/{id}/run` | Execute workflow |
| `POST /v1/analysis/roi` | Quick ROI calculation |
| `POST /v1/analysis/whitespace` | Gap analysis |
| `POST /v1/cases` | Generate business case |

## Workflows

1. **ROICalculator**: Calculates ROI from formulas with prospect data
2. **Whitespace**: Identifies gaps between needs and capabilities
3. **BusinessCase**: Generates full business case documents
4. **Orchestrator**: Multi-agent coordination

## Tools (24 Skills)

- **Knowledge** (6): `query_graph`, `semantic_search`, `get_entity`, etc.
- **Calculation** (4): `evaluate_formula`, `calculate_roi`, etc.
- **CRM** (4): `get_prospect_data`, `update_opportunity`, etc.
- **Generation** (4): `generate_section`, `create_chart`, etc.
- **Integration** (4): `send_notification`, `create_task`, etc.
- **Utility** (2): `validate_input`, `format_currency`

## License

## Secure service-to-service configuration

- Production/staging **must** configure explicit `LAYER{1,2,3,5}_API_URL` values; insecure HTTP defaults are not used.
- Canonical path is HTTPS to in-cluster service FQDNs (for example, `https://layer1-ingestion.value-fabric.svc.cluster.local:8000`).
- Service-mesh HTTP exceptions are allowed only when `SERVICE_MESH_MTLS_ENABLED=true` and mesh-level mTLS is enforced.
- Local development can use HTTP endpoints only with explicit `ALLOW_INSECURE_SERVICE_HTTP_IN_DEVELOPMENT=true`.

Proprietary - Value Fabric Enterprise Platform
