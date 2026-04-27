# Layer 4 Tool Inventory Report

Canonical source: `create_default_registry()` registration calls that populate `ToolRegistry`.

## 1) Externally invocable tools

These are the tools directly registered via `registry.register(...)` in `create_default_registry()`.

| # | Registered class | Tool name (runtime) | Source |
|---|------------------|---------------------|--------|
| 1 | `QueryGraphTool` | `query_graph` | `knowledge_tools.QueryGraphTool` |
| 2 | `SemanticSearchTool` | `semantic_search` | `knowledge_tools.SemanticSearchTool` |
| 3 | `GetEntityTool` | `get_entity` | `knowledge_tools.GetEntityTool` |
| 4 | `GetRelationshipsTool` | `get_relationships` | `knowledge_tools.GetRelationshipsTool` |
| 5 | `TraverseTreeTool` | `traverse_tree` | `knowledge_tools.TraverseTreeTool` |
| 6 | `FindPathsTool` | `find_paths` | `knowledge_tools.FindPathsTool` |
| 7 | `EvaluateFormulaTool` | `evaluate_formula` | `calculation_tools.EvaluateFormulaTool` |
| 8 | `CalculateROITool` | `calculate_roi` | `calculation_tools.CalculateROITool` |
| 9 | `CompareBenchmarksTool` | `compare_benchmarks` | `calculation_tools.CompareBenchmarksTool` |
| 10 | `SensitivityAnalysisTool` | `sensitivity_analysis` | `calculation_tools.SensitivityAnalysisTool` |
| 11 | `GetProspectDataTool` | `get_prospect_data` | `crm_tools.GetProspectDataTool` |
| 12 | `UpdateOpportunityTool` | `update_opportunity` | `crm_tools.UpdateOpportunityTool` |
| 13 | `FetchInteractionHistoryTool` | `fetch_interaction_history` | `crm_tools.FetchInteractionHistoryTool` |
| 14 | `ScoreLeadTool` | `score_lead` | `crm_tools.ScoreLeadTool` |
| 15 | `GenerateSectionTool` | `generate_section` | `generation_tools.GenerateSectionTool` |
| 16 | `CreateChartTool` | `create_chart` | `generation_tools.CreateChartTool` |
| 17 | `FormatTableTool` | `format_table` | `generation_tools.FormatTableTool` |
| 18 | `AssembleDocumentTool` | `assemble_document` | `generation_tools.AssembleDocumentTool` |
| 19 | `DocumentExportTool` | `export_document` | `document_export.DocumentExportTool` |
| 20 | `SendNotificationTool` | `send_notification` | `integration_tools.SendNotificationTool` |
| 21 | `CreateTaskTool` | `create_task` | `integration_tools.CreateTaskTool` |
| 22 | `ScheduleMeetingTool` | `schedule_meeting` | `integration_tools.ScheduleMeetingTool` |
| 23 | `ExportToCRMTool` | `export_to_crm` | `integration_tools.ExportToCRMTool` |
| 24 | `ValidateInputTool` | `validate_input` | `utility_tools.ValidateInputTool` |
| 25 | `FormatCurrencyTool` | `format_currency` | `utility_tools.FormatCurrencyTool` |
| 26 | `AnalyzeCompetitionTool` | `analyze_competition` | `competitive_tools.AnalyzeCompetitionTool` |

## 2) Internal/base helpers (not externally invocable registry entries)

| Symbol | File |
|--------|------|
| `BaseTool` | `value-fabric/layer4-agents/src/tools/registry.py` |
| `PDFGenerator` | `value-fabric/layer4-agents/src/tools/document_export.py` |
| `SafeExpressionEvaluator` | `value-fabric/layer4-agents/src/tools/calculation_tools.py` |
| `TenantAwareTool` | `value-fabric/layer4-agents/src/tools/registry.py` |
| `ToolError` | `value-fabric/layer4-agents/src/tools/registry.py` |
| `ToolNotFoundError` | `value-fabric/layer4-agents/src/tools/registry.py` |
| `ToolRegistry` | `value-fabric/layer4-agents/src/tools/registry.py` |
| `ToolValidationError` | `value-fabric/layer4-agents/src/tools/registry.py` |
| `analyze_entity` | `value-fabric/layer4-agents/src/tools/workflows.py` |
| `compute_metrics` | `value-fabric/layer4-agents/src/tools/analytics.py` |
| `count_entities` | `value-fabric/layer4-agents/src/tools/analytics.py` |
| `delete_entity` | `value-fabric/layer4-agents/src/tools/knowledge.py` |
| `get_all_tools` | `value-fabric/layer4-agents/src/tools/registry.py` |
| `get_available_tools` | `value-fabric/layer4-agents/src/tools/registry.py` |
| `get_entity` | `value-fabric/layer4-agents/src/tools/knowledge.py` |
| `get_global_registry` | `value-fabric/layer4-agents/src/tools/registry.py` |
| `get_tool_metadata` | `value-fabric/layer4-agents/src/tools/registry.py` |
| `list_entities` | `value-fabric/layer4-agents/src/tools/knowledge.py` |
| `read_and_update` | `value-fabric/layer4-agents/src/tools/workflows.py` |
| `read_file` | `value-fabric/layer4-agents/src/tools/files.py` |
| `reset_global_registry` | `value-fabric/layer4-agents/src/tools/registry.py` |
| `search_entities` | `value-fabric/layer4-agents/src/tools/knowledge.py` |
| `suspend_tenant` | `value-fabric/layer4-agents/src/tools/admin.py` |
| `tool` | `value-fabric/layer4-agents/src/tools/registry.py` |
| `update_entity` | `value-fabric/layer4-agents/src/tools/knowledge.py` |

## 3) Aliases / duplicate names across files

### Duplicate class names (exact)
- None detected.

### Semantic aliases / naming overlap

Overlaps are grouped by normalized name (case-folded, trailing `Tool` removed).

- `getentity`: `GetEntityTool (knowledge_tools.py)`, `get_entity (knowledge.py)`

Notable overlap requested for review:
- `knowledge.py` function `get_entity` overlaps conceptually with `knowledge_tools.py` class `GetEntityTool`.
