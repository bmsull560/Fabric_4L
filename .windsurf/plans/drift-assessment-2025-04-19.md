# Drift Assessment Report 2025-04-19

## Summary
- **Total drift instances**: 5
- **Critical**: 2 | **Warning**: 2 | **Info**: 1
- **Assessment date**: 2025-04-19
- **Layers analyzed**: L1, L2, L3, L4, Frontend

---

## OpenAPI Contract Drift

| Route | Issue | Severity | Fix Required |
|-------|-------|----------|--------------|
| `/v1/formulas/{id}/versions` | Missing `security: HTTPBearer` block in OpenAPI | Warning | Regenerate OpenAPI spec |
| `/v1/formulas/{id}/governance` | Missing `security: HTTPBearer` block in OpenAPI | Warning | Regenerate OpenAPI spec |
| `/v1/formulas/{id}/dependencies` | Missing `security: HTTPBearer` block in OpenAPI | Warning | Regenerate OpenAPI spec |
| `/v1/formulas/{id}/validate` | Missing `security: HTTPBearer` block in OpenAPI | Warning | Regenerate OpenAPI spec |
| `/v1/graph/subgraph` | **Path mismatch**: Backend has `/v1/graph/subgraph`, Frontend calls `/subgraph` via L3 client with base `/api/v1/graph` | **Critical** | Align path conventions |

### Evidence

**Git diff (OpenAPI security drift)**:
```diff
+        "security": [
+          {
+            "HTTPBearer": []
+          }
+        ]
```

Multiple formula governance endpoints are missing security documentation in the OpenAPI spec despite having authentication in implementation.

---

## Frontend/Backend Drift

| Hook | Expected | Actual | Impact |
|------|----------|--------|--------|
| `useSubgraph` (`useGraphQuery.ts:311`) | `GET /subgraph` → calls `/api/v1/graph/subgraph` | Backend OpenAPI documents `/v1/graph/subgraph` | **Critical** - Path prefix mismatch (`/api` vs `/v1`) |
| `useFormulaApprovals` (`useFormulas.ts:105`) | `GET /formulas/approvals/pending` | OpenAPI has `FormulasRegistryResponse` wrapper | Warning - Schema structure mismatch |
| `useEntities` | `GraphNode[]` with alias fields | Backend uses `label`/`type`/`confidence`, frontend expects `name`/`entity_type`/`confidence_score` | Warning - Field alias handling |

### Evidence

**Frontend API Client Configuration** (`frontend/client/src/api/client.ts:3-12`):
```typescript
const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';
const LAYER_PREFIXES = {
  l3: import.meta.env.VITE_L3_PREFIX || '/graph',
  // ...
};
// Full URL: /api/v1/graph + /subgraph = /api/v1/graph/subgraph
```

**Backend OpenAPI Path** (`contracts/openapi/layer3-knowledge.json:4868`):
```json
"/v1/graph/subgraph": {
  "get": { ... }
}
```

**Mismatch**: Frontend expects API at `/api/v1/*` but OpenAPI documents `/v1/*`.

---

## Cross-Layer Integration

| Flow | Status | Evidence |
|------|--------|----------|
| L3 → Frontend (Graph Query) | ⚠️ **At Risk** | Path prefix drift may cause 404s |
| L3 → Frontend (Formulas) | ✅ **Functional** | Zod validation schemas aligned |
| L3 → Frontend (Entity Context) | ✅ **Functional** | Contract tests pass |
| L2 → L3 (Ingestion) | ✅ **Functional** | Ingestion tests passing |
| L4 → Frontend (Workflows) | ✅ **Functional** | SSE endpoints documented |

### Evidence

**Contract Test Results**:
- 22 passed, 1 failed, 2 skipped
- Failed: SDK test (`test_client_init_with_api_key`) - unrelated to API drift
- Graph contract tests pass for schema validation

**Schema Alignment**:
- `frontend/client/src/lib/validation/schemas.ts` has proper Zod schemas matching OpenAPI
- `SubgraphResponseSchema` validates `root_entity_id`, `nodes`, `edges`, `depth`, `stats`

---

## Schema Evolution Audit

| Layer | Schema Status | Drift Detected |
|-------|---------------|----------------|
| L3 Graph | GraphNode uses `label`/`type`/`confidence` | Frontend expects `name`/`entity_type`/`confidence_score` - **Aliases in place** |
| L3 Formulas | `FormulaMetadata` schema | ✅ Aligned |
| L3 Search | `SearchResponse` schema | ✅ Aligned |
| L4 Workflows | `WorkflowStatusResponse` | ✅ Aligned |

### Field Alias Strategy (Documented)

From `test_l3_graph_contract.py:239-243`:
```python
# NOTE: Backend provides backward-compatible alias fields:
# - 'name' alias for 'label' (frontend expects 'name')
# - 'entity_type' alias for 'type' (frontend expects 'entity_type')
# - 'confidence_score' alias for 'confidence' (frontend expects 'confidence_score')
```

The Pydantic models correctly output both legacy and alias fields via `model_dump()` override.

---

## Recommended Actions

### [P0] Fix Critical Path Prefix Drift
**Owner**: Backend + DevOps
**Action**: 
1. Align API base path conventions:
   - Option A: Backend mounts routes at `/api/v1/*` 
   - Option B: Frontend changes `API_BASE` from `/api/v1` to `/v1`
2. Update environment variable docs in `ENVIRONMENT.md`
3. Verify with end-to-end test

**Impact**: Without this fix, Graph Explorer and subgraph queries will 404.

### [P1] Regenerate OpenAPI Specs
**Owner**: Backend
**Action**: Run `python scripts/export_openapi.py` and commit regenerated specs with security blocks.

**Commands**:
```bash
python scripts/export_openapi.py
git diff contracts/openapi/
# Review and commit if changes are acceptable
```

### [P2] Add Contract Test for Path Alignment
**Owner**: QA/Testing
**Action**: Add test to verify frontend API client base URLs match OpenAPI server URLs:

```python
def test_frontend_backend_path_alignment():
    """Verify frontend API client and OpenAPI paths align."""
    # Frontend expects: /api/v1/graph/subgraph
    # OpenAPI has: /v1/graph/subgraph
    # These must match after deployment routing
```

### [P2] Document Field Alias Strategy
**Owner**: Documentation
**Action**: Add explicit field mapping documentation to API_REFERENCE.md:
- Backend field → Frontend field mapping
- Alias resolution in Pydantic models

---

## Verification Commands

```bash
# Run contract tests
python -m pytest tests/contract/ -v

# Regenerate OpenAPI
python scripts/export_openapi.py

# Check for drift
git diff contracts/openapi/

# Frontend type check
cd frontend/client && npx tsc --noEmit

# Frontend tests
cd frontend/client && npm test
```

---

## Safety Checklist

- [ ] Critical drift items have assigned owners
- [ ] Path prefix drift resolved before production deploy
- [ ] OpenAPI specs regenerated and reviewed
- [ ] Integration tests pass end-to-end
- [ ] Frontend type-check passes
- [ ] Breaking changes documented (if any)

---

## Notes

1. **Security drift is non-breaking**: Missing security blocks in OpenAPI don't affect runtime behavior - they only affect documentation/contract completeness.

2. **Field aliases are working**: The alias strategy (`label`→`name`, `type`→`entity_type`, etc.) is correctly implemented in Pydantic models and verified by contract tests.

3. **Path prefix is the real issue**: The `/api` vs `/v1` path prefix mismatch is the only critical item that could cause runtime failures.

4. **Zod validation is in place**: Frontend has robust runtime validation with `validateOrThrow()` pattern that will catch schema mismatches early.
