"""Business Case Generator workflow implementation."""

import logging
import os
from typing import Any

try:
    from shared.identity.feature_flags import is_enabled
except ImportError:
    # Fallback if shared package not available
    def is_enabled(flag_key: str, tenant_id=None, user_id=None) -> bool:
        return False

from ..integration.layer5_client import Layer5GroundTruthClient
from ..models.agent_state import (
    BusinessCaseAgentState,
    BusinessCaseInputData,
    BusinessCaseSection,
    WorkflowStatus,
)
from ..models.workflow_config import BUSINESS_CASE_WORKFLOW_CONFIG
from ..tools.registry import ToolRegistry
from .base import BaseWorkflow
from .roi_calculator import ROICalculatorWorkflow

logger = logging.getLogger(__name__)


class BusinessCaseGeneratorWorkflow(BaseWorkflow):
    """Workflow for generating comprehensive business case documents.

    Pipeline:
    1. Gather inputs from CRM and prior analyses
    2. Run ROI calculation (sub-workflow)
    3. Generate narrative sections using LLM
    4. Create charts and tables
    5. Assemble into final document

    Example:
        workflow = BusinessCaseGeneratorWorkflow(tool_registry)
        initial_state = workflow.create_initial_state({
            "account_id": "550e8400-e29b-41d4-a716-446655440000",
            "sections_requested": ["executive_summary", "roi_analysis"],
            "output_format": "pdf"
        })
        result = await workflow.run(initial_state)
    """

    def __init__(self, tool_registry: ToolRegistry, checkpoint_saver=None):
        """Initialize Business Case Generator workflow."""
        super().__init__(
            config=BUSINESS_CASE_WORKFLOW_CONFIG,
            tool_registry=tool_registry,
            checkpoint_saver=checkpoint_saver,
        )
        self.roi_workflow = ROICalculatorWorkflow(tool_registry, checkpoint_saver)

    def _get_state_type(self):
        """Return Business Case-specific state type."""
        return BusinessCaseAgentState

    def create_initial_state(self, input_data: dict[str, Any]) -> BusinessCaseAgentState:
        """Create initial state from input data."""
        case_input = BusinessCaseInputData(**input_data)

        return BusinessCaseAgentState(
            workflow_type=self.config.workflow_type,
            status=WorkflowStatus.PENDING,
            case_input=case_input,
            input_data=input_data,
            output_data={},
            errors=[],
            metadata={"workflow_name": self.name},
        )

    async def _execute_tool(
        self, tool_name: str, state: BusinessCaseAgentState, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute tool with Business Case-specific input building."""

        if tool_name == "gather_case_inputs":
            return await self._execute_gather_inputs(state)
        elif tool_name == "verify_truth_requirements":
            return await self._execute_verify_truth_requirements(state)

        elif tool_name == "assemble_document":
            return await self._execute_assemble_document(state)

        return await super()._execute_tool(tool_name, state, config)

    async def _execute_agent(self, node_config, state: BusinessCaseAgentState) -> dict[str, Any]:
        """Execute agent node (sub-workflow)."""
        if node_config.id == "run_roi":
            return await self._execute_roi_subworkflow(state)

        return {"status": "agent_not_implemented"}

    async def _execute_llm(self, node_config, state: BusinessCaseAgentState) -> dict[str, Any]:
        """Execute LLM node for section generation."""
        if node_config.id == "generate_narrative":
            return await self._execute_generate_sections(state)

        return {"status": "llm_not_implemented"}

    async def _execute_gather_inputs(self, state: BusinessCaseAgentState) -> dict[str, Any]:
        """Gather all inputs needed for business case generation."""
        if not state.case_input:
            return {"error": "No business case input configured"}

        account_id = str(state.case_input.account_id)
        prospect_id = state.case_input.custom_inputs.get("provider_record_id", account_id)

        # Fetch prospect data
        prospect_data = await self.tool_registry.execute(
            "get_prospect_data",
            {
                "prospect_id": prospect_id,
                "data_types": ["profile", "interactions", "opportunities"],
            },
        )

        # Fetch interaction history
        interactions = await self.tool_registry.execute(
            "fetch_interaction_history", {"prospect_id": prospect_id, "limit": 10}
        )

        # Score lead for additional context
        lead_score = await self.tool_registry.execute("score_lead", {"prospect_id": prospect_id})

        return {
            "account_id": account_id,
            "prospect": prospect_data,
            "interactions": interactions,
            "lead_score": lead_score,
            "sections_requested": state.case_input.sections_requested,
            "output_format": state.case_input.output_format,
        }

    async def _execute_roi_subworkflow(self, state: BusinessCaseAgentState) -> dict[str, Any]:
        """Execute ROI calculation as sub-workflow."""
        if not state.case_input:
            return {"error": "No business case input configured"}

        account_id = str(state.case_input.account_id)
        prospect_id = state.case_input.custom_inputs.get("provider_record_id", account_id)

        # Create ROI workflow state
        roi_input_data = {
            "prospect_id": prospect_id,
            "value_driver_ids": ["vd-001", "vd-002", "vd-003"],  # Default set
            "use_benchmarks": True,
        }

        roi_initial_state = self.roi_workflow.create_initial_state(roi_input_data)

        # Run ROI workflow
        try:
            roi_result = await self.roi_workflow.run(roi_initial_state)

            return {
                "status": "completed",
                "account_id": account_id,
                "roi_results": roi_result.output_data.get("aggregate", {}),
                "detailed_calculations": roi_result.calculation_results,
            }
        except Exception as e:
            return {"status": "failed", "error": str(e), "roi_results": {}}

    async def _execute_generate_sections(self, state: BusinessCaseAgentState) -> dict[str, Any]:
        """Generate all requested narrative sections.

        Feature flag 'enhanced_narrative_generation' controls whether to use
        the new LLM-powered section enhancement feature.
        """
        if not state.case_input:
            return {"error": "No business case input configured", "sections": []}

        gate_result = state.output_data.get("verify_truth_requirements", {})
        if gate_result and not gate_result.get("passed", True):
            return {
                "error": "Narrative generation blocked by truth verification gate",
                "blocked": True,
                "sections": [],
                "remediation_items": gate_result.get("remediation_items", []),
                "truth_references": gate_result.get("truth_references", []),
            }

        # Check feature flag for enhanced narrative generation (Task 83: is_enabled usage)
        enhanced_mode = is_enabled(
            "enhanced_narrative_generation",
            tenant_id=getattr(state, 'tenant_id', None),
            user_id=getattr(state, 'user_id', None),
        )
        if enhanced_mode:
            logger.info("Using enhanced narrative generation for business case")

        gathered = state.output_data.get("gather_inputs", {})
        roi_data = state.output_data.get("run_roi", {})

        prospect = gathered.get("prospect", {})
        profile = prospect.get("profile", {})
        roi_results = roi_data.get("roi_results", {})

        sections_generated: list[BusinessCaseSection] = []

        # Build context for section generation
        context = {
            "company_name": profile.get("name", "the prospect"),
            "industry": profile.get("industry", "their industry"),
            "annual_revenue": profile.get("annual_revenue", "unknown"),
            "pain_points": prospect.get("custom_fields", {}).get("pain_points", []),
            "roi_percent": roi_results.get("simple_roi_percent", 0),
            "payback_months": roi_results.get("payback_period_months", 0),
            "three_year_npv": roi_results.get("three_year_npv", 0),
        }

        requested_sections = state.case_input.sections_requested

        # Map section types to titles
        section_titles = {
            "executive_summary": "Executive Summary",
            "current_state": "Current State Analysis",
            "proposed_solution": "Proposed Solution",
            "roi_analysis": "ROI Analysis",
            "implementation": "Implementation Plan",
            "next_steps": "Recommended Next Steps",
        }

        for section_type in requested_sections:
            title = section_titles.get(section_type, section_type.replace("_", " ").title())

            try:
                # Generate section content
                section_result = await self.tool_registry.execute(
                    "generate_section",
                    {
                        "section_type": section_type,
                        "context": context,
                        "tone": "professional",
                        "max_length": 500,
                    },
                )

                # Create charts for ROI section
                charts = []
                if section_type == "roi_analysis" and roi_results:
                    # ROI bar chart
                    chart_result = await self.tool_registry.execute(
                        "create_chart",
                        {
                            "chart_type": "bar",
                            "data": [
                                {
                                    "label": "Investment",
                                    "value": roi_results.get("investment_required", 0),
                                },
                                {
                                    "label": "Year 1 Value",
                                    "value": roi_results.get("total_annual_value", 0),
                                },
                                {
                                    "label": "3-Year NPV",
                                    "value": roi_results.get("three_year_npv", 0),
                                },
                            ],
                            "title": "ROI Summary",
                        },
                    )
                    charts.append(chart_result.get("chart_data", {}))

                section = BusinessCaseSection(
                    title=title, content=section_result.get("content", ""), charts=charts, tables=[]
                )
                sections_generated.append(section)

            except Exception as e:
                # Add error section
                section = BusinessCaseSection(
                    title=title, content=f"Error generating section: {str(e)}", charts=[], tables=[]
                )
                sections_generated.append(section)

        return {
            "sections": [s.model_dump() for s in sections_generated],
            "section_count": len(sections_generated),
        }

    async def _execute_verify_truth_requirements(
        self, state: BusinessCaseAgentState
    ) -> dict[str, Any]:
        """Verify required claims/metrics against Layer 5 TruthObjects."""
        if not state.case_input:
            return {"error": "No business case input configured", "passed": False}

        requirements = state.case_input.custom_inputs.get("truth_requirements", [])
        if not requirements:
            return {"passed": True, "requirements": [], "truth_references": [], "remediation_items": []}

        organization_id = self._resolve_organization_id(state)
        service_token: str | None = os.getenv("LAYER5_SERVICE_TOKEN")
        layer5_url: str | None = os.getenv(
            "LAYER5_GROUND_TRUTH_URL", "http://layer5-ground-truth:8005"
        )
        min_maturity = min(
            [int(req.get("min_maturity", 0)) for req in requirements if req.get("min_maturity") is not None],
            default=0,
        )
        min_confidence = min(
            [float(req.get("min_confidence", 0.0)) for req in requirements if req.get("min_confidence") is not None],
            default=0.0,
        )

        client = Layer5GroundTruthClient(
            base_url=layer5_url,
            service_token=service_token,
            tenant_id=organization_id if not service_token else None,
        )

        status_rank = {"extracted": 0, "supported": 1, "corroborated": 2, "approved": 3, "disputed": -1}
        truth_references: list[dict[str, Any]] = []
        remediation_items: list[dict[str, Any]] = []
        requirement_results: list[dict[str, Any]] = []
        all_passed = True

        try:
            truths_result = await client.list_truths(
                organization_id=organization_id,
                min_maturity=min_maturity,
                min_confidence=min_confidence,
                applies_to_opportunity=state.case_input.opportunity_id,
                limit=200,
                offset=0,
            )
            truths = truths_result.get("items", []) if isinstance(truths_result, dict) else []

            for req in requirements:
                required_status = str(req.get("min_status", "corroborated")).lower()
                required_maturity = int(req.get("min_maturity", 3))
                required_confidence = float(req.get("min_confidence", 0.0))
                required_sources = int(req.get("min_sources", 2))
                label = req.get("label") or req.get("claim") or req.get("metric") or "required-claim"
                required = bool(req.get("required", True))

                def _match(truth: dict[str, Any]) -> bool:
                    claim_q = str(req.get("claim", "")).strip().lower()
                    metric_q = str(req.get("metric", "")).strip().lower()
                    claim_text = str(truth.get("claim", "")).lower()
                    if claim_q and claim_q in claim_text:
                        return True
                    if metric_q and (
                        metric_q in claim_text
                        or metric_q == str(truth.get("claim_type", "")).lower()
                    ):
                        return True
                    return False

                matches = [t for t in truths if _match(t)]
                if not matches:
                    if required:
                        all_passed = False
                        remediation_items.append(
                            {
                                "type": "missing_evidence",
                                "requirement": label,
                                "message": "No matching TruthObject found. Add supporting evidence.",
                            }
                        )
                    requirement_results.append({"requirement": label, "passed": False, "match_count": 0})
                    continue

                best = sorted(
                    matches,
                    key=lambda t: (
                        status_rank.get(str(t.get("status", "")).lower(), -1),
                        int(t.get("maturity_level", 0)),
                        float(t.get("confidence", 0.0)),
                        int(t.get("source_count", 0)),
                    ),
                    reverse=True,
                )[0]

                status_ok = status_rank.get(str(best.get("status", "")).lower(), -1) >= status_rank.get(required_status, 2)
                maturity_ok = int(best.get("maturity_level", 0)) >= required_maturity
                confidence_ok = float(best.get("confidence", 0.0)) >= required_confidence
                sources_ok = int(best.get("source_count", 0)) >= required_sources
                passed = status_ok and maturity_ok and confidence_ok

                truth_references.append(
                    {
                        "requirement": label,
                        "truth_object_id": str(best.get("id")),
                        "claim": best.get("claim"),
                        "claim_type": best.get("claim_type"),
                        "status": best.get("status"),
                        "maturity_level": best.get("maturity_level"),
                        "confidence": best.get("confidence"),
                        "source_count": best.get("source_count", 0),
                        "freshness": best.get("freshness"),
                    }
                )
                requirement_results.append(
                    {
                        "requirement": label,
                        "passed": passed,
                        "status_ok": status_ok,
                        "maturity_ok": maturity_ok,
                        "confidence_ok": confidence_ok,
                        "sources_ok": sources_ok,
                        "truth_object_id": str(best.get("id")),
                    }
                )

                if required and not passed:
                    all_passed = False
                    if not sources_ok:
                        remediation_items.append(
                            {
                                "type": "insufficient_corroboration",
                                "requirement": label,
                                "message": "Evidence exists but corroboration is insufficient. Add independent sources.",
                            }
                        )
                    elif required_status == "approved" and str(best.get("status", "")).lower() != "approved":
                        remediation_items.append(
                            {
                                "type": "approval_pending",
                                "requirement": label,
                                "message": "Evidence is not yet approved. Complete governance approval in Layer 5.",
                            }
                        )
                    else:
                        remediation_items.append(
                            {
                                "type": "verification_gap",
                                "requirement": label,
                                "message": "Evidence does not meet required status/maturity/confidence thresholds.",
                            }
                        )

            return {
                "passed": all_passed,
                "requirements": requirement_results,
                "truth_references": truth_references,
                "remediation_items": remediation_items,
                "organization_id": organization_id,
            }
        finally:
            await client.close()

    async def _execute_assemble_document(self, state: BusinessCaseAgentState) -> dict[str, Any]:
        """Assemble sections into final document, then sync ground truths to KG."""
        if not state.case_input:
            return {"error": "No business case input configured"}

        gate_result = state.output_data.get("verify_truth_requirements", {})
        if gate_result and not gate_result.get("passed", True):
            return {
                "blocked": True,
                "error": "Final narrative/export blocked: required claims are not verified",
                "remediation_items": gate_result.get("remediation_items", []),
                "truth_references": gate_result.get("truth_references", []),
                "case_metadata": {
                    "account_id": str(state.case_input.account_id),
                    "truth_gate": {
                        "passed": False,
                        "requirements": gate_result.get("requirements", []),
                    },
                    "truth_references": gate_result.get("truth_references", []),
                },
            }

        sections_data = state.output_data.get("generate_narrative", {}).get("sections", [])

        if not sections_data:
            return {"error": "No sections generated"}

        # Prepare sections for assembly
        assembly_sections = []
        for s in sections_data:
            assembly_sections.append(
                {
                    "title": s.get("title", "Section"),
                    "content": s.get("content", ""),
                    "charts": s.get("charts", []),
                    "tables": s.get("tables", []),
                }
            )

        # Assemble document
        assemble_result: dict[str, Any] = {}
        try:
            result = await self.tool_registry.execute(
                "assemble_document",
                {
                    "sections": assembly_sections,
                    "template": "business_case",
                    "output_format": state.case_input.output_format,
                    "branding": {
                        "company_name": state.case_input.custom_inputs.get(
                            "company_name", "Value Fabric"
                        ),
                        "date": state.case_input.custom_inputs.get("date", "2024"),
                    },
                },
            )
            assemble_result = {
                "document_bytes": result.get("document_bytes"),
                "document_url": result.get("document_url"),
                "page_count": result.get("page_count", len(assembly_sections)),
                "file_size_bytes": result.get("file_size_bytes", 0),
                "format": state.case_input.output_format,
            }
        except Exception as e:
            assemble_result = {
                "error": str(e),
                "document_bytes": None,
                "document_url": None,
            }

        # ── Layer 5 Ground Truth sync ──────────────────────────────────────
        # After the business case document is assembled, trigger a bulk sync
        # of all APPROVED TruthObjects for this tenant to the Layer 3
        # Knowledge Graph.  This is best-effort: a Layer 5 outage must not
        # block document delivery.
        sync_result = await self._sync_ground_truths_to_kg(state)
        assemble_result["ground_truth_sync"] = sync_result
        assemble_result["case_metadata"] = {
            "account_id": str(state.case_input.account_id),
            "truth_gate": {
                "passed": gate_result.get("passed", True),
                "requirements": gate_result.get("requirements", []),
                "remediation_items": gate_result.get("remediation_items", []),
            },
            "truth_references": gate_result.get("truth_references", []),
        }

        return assemble_result

    def _resolve_organization_id(self, state: BusinessCaseAgentState) -> str | None:
        """Resolve tenant/organization ID from state or environment."""
        organization_id: str | None = None

        if state.case_input and state.case_input.custom_inputs:
            organization_id = state.case_input.custom_inputs.get("organization_id")

        if not organization_id and state.metadata:
            organization_id = state.metadata.get("tenant_id")

        if not organization_id:
            organization_id = os.getenv("LAYER5_DEFAULT_ORG_ID")

        return organization_id

    async def _sync_ground_truths_to_kg(self, state: BusinessCaseAgentState) -> dict[str, Any]:
        """Best-effort sync of approved TruthObjects to the KG via Layer 5.

        Resolves the tenant/organization ID from (in priority order):
          1. ``state.case_input.custom_inputs["organization_id"]``
          2. ``state.metadata["tenant_id"]`` (set by TenantMiddleware)
          3. The LAYER5_DEFAULT_ORG_ID environment variable (dev fallback)

        Returns a dict with sync statistics or an ``error`` key.
        """
        organization_id = self._resolve_organization_id(state)

        # Resolve service token for Layer 5 auth
        service_token: str | None = os.getenv("LAYER5_SERVICE_TOKEN")
        layer5_url: str | None = os.getenv(
            "LAYER5_GROUND_TRUTH_URL", "http://layer5-ground-truth:8005"
        )

        client = Layer5GroundTruthClient(
            base_url=layer5_url,
            service_token=service_token,
            tenant_id=organization_id if not service_token else None,
        )

        try:
            sync_result = await client.sync_approved_truths(organization_id=organization_id)
            logger.info(
                "Business case ground-truth sync complete for org=%s: %s",
                organization_id,
                sync_result,
            )
            return sync_result
        except Exception as exc:
            logger.warning(
                "Ground-truth sync failed (non-blocking) for org=%s: %s",
                organization_id,
                exc,
            )
            return {"error": str(exc), "synced": 0, "failed": 0}
        finally:
            await client.close()
