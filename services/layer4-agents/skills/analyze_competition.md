---
name: analyze_competition
description: Analyzes competitive alternatives and produces structured competitive intelligence
---

# Analyze Competition

Analyze competitive alternatives and produce a structured CompetitiveIntelArtifact with economic differences, comparative scenarios, and confidence scores.

## Parameters

- `context_artifact_id`: string — ID of the ContextArtifact (required)
- `tenant_id`: string — Tenant identifier (required)
- `workspace_id`: string — Workspace identifier (required)
- `prospect_industry`: string — Industry vertical (optional)
- `known_competitors`: array — Competitor names from discovery (optional)
- `known_incumbent`: string — Current vendor being replaced (optional)
- `deal_context`: string — Deal summary text (optional)
- `baselines_to_evaluate`: array — Which baselines to analyze (optional)

## Steps

1. Query Knowledge Graph for competitor data
2. Extract economic differences via LLM
3. Score confidence for each claim
4. Flag unsupported claims
5. Build comparative scenarios
6. Return CompetitiveIntelArtifact

## Output

Returns AnalyzeCompetitionOutput with:
- `artifact`: CompetitiveIntelArtifact
- `baselines_evaluated`: List of analyzed baselines
- `total_differences_found`: Count of differences
- `unsupported_claim_count`: Claims needing review
- `defensibility_score`: Overall confidence score
- `agent_notes`: Analysis summary
