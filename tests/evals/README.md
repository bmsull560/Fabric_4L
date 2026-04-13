# Agent Evaluations

This directory contains **golden-trace evaluations** for agent skills and workflows.

## What are evals?

Evals test that agent skills produce correct, consistent output given known inputs.
Unlike unit tests (which test code logic), evals test **behavioral contracts**:
- Does `semantic_search` return the right entities for a known query?
- Does `evaluate_formula` produce the expected ROI calculation?
- Does the Business Analyst Agent produce a complete business case?

## Structure

```
tests/evals/
  conftest.py         Shared fixtures (mock knowledge graph, mock LLM)
  fixtures/           Golden trace fixtures (input → expected output)
    semantic_search_traces.json
    evaluate_formula_traces.json
  skills/             Skill-level evaluations
    test_semantic_search.py
    test_evaluate_formula.py
    test_graph_traverse.py
  test_business_analyst_agent.py   Full agent evaluation
```

## Running evals

```bash
# Fast evals (no real LLM calls, uses recorded responses)
make evals

# Full eval suite including real LLM calls (costs money, slow)
make evals-full
```

## Adding a new eval

1. Add a fixture file in `fixtures/` with input/expected pairs.
2. Create a test in `skills/test_<skill_name>.py`.
3. Mark tests that require real LLM calls with `@pytest.mark.slow`.

## Fixture format

```json
{
  "version": "1.0",
  "skill": "skill_name",
  "traces": [
    {
      "id": "trace-001",
      "description": "Human-readable description of what this tests",
      "input": { ... },
      "expected_output": { ... },
      "assertions": ["has_results", "score_above_threshold"]
    }
  ]
}
```
