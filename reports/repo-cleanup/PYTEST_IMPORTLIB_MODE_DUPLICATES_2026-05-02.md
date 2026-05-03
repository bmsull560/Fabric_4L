# Pytest Importlib Mode Duplicate Test Files Report
**Date:** 2026-05-02
**Purpose:** Document duplicate test file names causing import file mismatch errors with --import-mode=importlib

## Summary

When running pytest with `--import-mode=importlib`, 30 additional collection errors were discovered across layer1-ingestion, layer2-extraction, and layer3-knowledge tests. These are "import file mismatch" errors caused by pytest's module caching when test files with identical names exist in different directories.

## Duplicate Test Files Identified

### High-Impact Duplicates (Multiple Services)

1. **test_tenant_isolation.py** - 3 copies
   - `services/layer3-knowledge/tests/test_tenant_isolation.py`
   - `services/layer4-agents/tests/test_tenant_isolation.py`
   - `tests/security/test_tenant_isolation.py`
   - **Impact:** All three files test tenant isolation in different contexts (Layer 3 knowledge graph, Layer 4 agents, root security tests)

2. **test_llm_cost_metrics.py** - 2 copies
   - `services/layer2-extraction/tests/test_llm_cost_metrics.py`
   - `services/layer4-agents/tests/test_llm_cost_metrics.py`
   - **Impact:** Both files test LLM cost metrics tracking in different layers (extraction vs agents)

3. **test_api.py** - 2 copies
   - `services/layer3-knowledge/tests/test_api.py`
   - `services/layer5-ground-truth/tests/test_api.py`
   - **Impact:** Both files test API endpoints in different services (knowledge vs ground truth)

### Additional Duplicates (Pack Tests)

The following duplicate test files exist across different value packs (ai-technology, energy-utilities, financial-services, life-sciences, manufacturing, retail-consumer, software):

- **test_formula_execution.py** - 7 copies (one per pack)
- **test_ontology_relationships.py** - 7 copies (one per pack)
- **test_pack_integrity.py** - 7 copies (one per pack)

**Impact:** These are intentional duplicates as each pack has its own test suite for formula execution, ontology relationships, and pack integrity. These are not problematic as they are in separate pack directories and should not conflict.

## CI Configuration Check

**Question:** Does CI use --import-mode=importlib?

**Status:** Needs investigation

**Action Required:** Check CI configuration files (`.github/workflows/*.yml`) to determine if pytest is run with `--import-mode=importlib`.

## Recommended Remediation Strategies

### Option 1: Rename Duplicate Files (Recommended for Service Duplicates)

For the high-impact service duplicates, rename files to be more specific:

1. **test_tenant_isolation.py** → 
   - `services/layer3-knowledge/tests/test_graph_tenant_isolation.py`
   - `services/layer4-agents/tests/test_agents_tenant_isolation.py`
   - `tests/security/test_security_tenant_isolation.py` (or keep as is)

2. **test_llm_cost_metrics.py** →
   - `services/layer2-extraction/tests/test_extraction_llm_cost_metrics.py`
   - `services/layer4-agents/tests/test_agents_llm_cost_metrics.py`

3. **test_api.py** →
   - `services/layer3-knowledge/tests/test_knowledge_api.py`
   - `services/layer5-ground-truth/tests/test_ground_truth_api.py`

### Option 2: Use Package Markers (Alternative)

Add `__init__.py` files to test directories to make them proper packages, which allows pytest to distinguish between test files with the same name in different packages.

### Option 3: Accept Default Import Mode (If CI Doesn't Use importlib)

If CI does not use `--import-mode=importlib`, these duplicates are not a launch blocker. The default pytest import mode is permissive and handles these duplicates correctly.

## Recommendation

**Immediate Action:** Investigate CI configuration to determine if `--import-mode=importlib` is used.

**If CI uses importlib mode:** Implement Option 1 (rename duplicate files) for the 3 high-impact service duplicates. The pack test duplicates can be left as-is since they are in separate directories and serve different purposes.

**If CI does not use importlib mode:** Mark this as a low-priority cleanup item. The duplicates are not blocking with the default pytest import mode.

## Next Steps

1. Check CI configuration for `--import-mode=importlib` usage
2. Based on findings, either:
   - Rename duplicate test files (if importlib mode is required)
   - Mark as low-priority cleanup (if importlib mode is not required)
3. Update documentation if renaming is implemented
