# **VALUE FABRIC: DEVELOPMENT RULES** (Quick Reference)

**Status:** Legacy Reference Material  
**Last Reviewed:** 2026-05-04  
**Note:** This document provides a quick reference for development rules. For current rule enforcement, see the YAML rule files in this directory (`hard-constraints.yaml`, `safety-rules.yaml`, `dependency-rules.yaml`, `style-rules.yaml`).

## **1. CODE QUALITY**
| Aspect | Rule |
|--------|------|
| **Python** | 3.11+, async/await for I/O, type hints mandatory (mypy strict) |
| **TypeScript** | Strict mode, no `any`, explicit return types |
| **Linting** | Ruff (Python), ESLint (TS) — zero warnings in CI |
| **Formatting** | Black (Python), Prettier (TS) — auto-format on save |
| **Imports** | Absolute only, grouped: stdlib → third-party → local |
| **Docstrings** | Google style, every public function |

### **Git Workflow**
- **Branch**: `layer-X/feature/description` or `fix/layer-X/bug-description`
- **Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- **PRs**: 2 approvals, tests pass, coverage doesn't decrease

---

## **2. TESTING**

### **Coverage Requirements**
| Layer | Minimum | Critical Paths |
|-------|---------|----------------|
| Layer 1 | 80% | Rate limiting, PII detection, robots.txt |
| Layer 2 | 85% | Schema validation, deduplication, RDF output |
| Layer 3 | 80% | GraphRAG retrieval, semantic queries, access control |
| Layer 4 | 75% | ROI calculation, document generation, provenance |

### **Test Pyramid**
```
        /\  E2E (5%) - Full workflows
       /  \
      /____\ Integration (15%) - Service boundaries
     /      \
    /________\ Unit (80%) - Functions, classes
```

### **CI/CD Gates**
- [ ] All unit tests pass
- [ ] Coverage >= minimum threshold
- [ ] Integration tests pass
- [ ] Security scan: no CRITICAL/HIGH vulnerabilities
- [ ] Linting: zero warnings
- [ ] Type checking: mypy/pyright pass

---

## **3. API DESIGN**
- **URLs**: Nouns, plural, kebab-case (`/capabilities`, `/use-cases`)
- **Methods**: GET, POST, PUT, DELETE, PATCH
- **Status codes**: 200, 201, 400, 401, 403, 404, 409, 422, 500
- **Content-Type**: `application/json` (default), `text/turtle` for RDF
- **Versioning**: URL-based `/v1/capabilities`, 6-month deprecation notice

### **Response Format**
```json
{
  "data": { ... },
  "meta": { "page": 1, "per_page": 20, "total": 150 },
  "links": { "self": "/capabilities?page=1", "next": "/capabilities?page=2" }
}
```

---

## **4. DOCUMENTATION**
- **README**: Every service — purpose, setup, testing, deployment
- **Docstrings**: Google style, all public functions
- **Comments**: Explain "why", not "what"
- **TODOs**: Include ticket number `TODO(TICKET-123): description`

### **Required Documents**
| Document | Location | Owner | Frequency |
|----------|----------|-------|-----------|
| ADRs | `/docs/adrs/` | Tech Lead | Per decision |
| API Reference | OpenAPI spec | API Owner | Per release |
| Runbook | `/docs/runbooks/` | SRE | Quarterly |

---

## **5. AI/LLM GOVERNANCE**

### **Model Usage**
| Use Case | Model | Temperature | Max Tokens |
|----------|-------|-------------|------------|
| Entity/Relation Extraction | GPT-4o / Claude 3.5 | 0.0 | 4000 |
| Summarization | GPT-4o-mini | 0.3 | 2000 |
| Business Case Generation | GPT-4o | 0.7 | 8000 |
| Code Generation | Claude 3.5 Sonnet | 0.2 | 4000 |

### **Safety Rules**
1. **No PII in prompts** — pre-process with detector
2. **Prompt versioning** — all in Git, versioned with app
3. **Output validation** — schema validation before using
4. **Confidence <0.8** — flag for review
5. **Evidence quotes** — every claim cites source text

---

**See `rules_ops.md` for Data Governance, Security, Observability, Deployment, Incident Response, and Performance Budgets.**

**Enforcement**: These rules are checked in CI/CD. Violations block merge.
