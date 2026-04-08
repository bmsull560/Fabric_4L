"""Business Case Generator workflow implementation."""

from typing import Any, Dict, List

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
            "prospect_id": "prospect-001",
            "sections_requested": ["executive_summary", "roi_analysis"],
            "output_format": "pdf"
        })
        result = await workflow.run(initial_state)
    """
    
    def __init__(
        self,
        tool_registry: ToolRegistry,
        checkpoint_saver=None
    ):
        """Initialize Business Case Generator workflow."""
        super().__init__(
            config=BUSINESS_CASE_WORKFLOW_CONFIG,
            tool_registry=tool_registry,
            checkpoint_saver=checkpoint_saver
        )
        self.roi_workflow = ROICalculatorWorkflow(tool_registry, checkpoint_saver)
    
    def _get_state_type(self):
        """Return Business Case-specific state type."""
        return BusinessCaseAgentState
    
    def create_initial_state(self, input_data: Dict[str, Any]) -> BusinessCaseAgentState:
        """Create initial state from input data."""
        case_input = BusinessCaseInputData(**input_data)
        
        return BusinessCaseAgentState(
            workflow_type=self.config.workflow_type,
            status=WorkflowStatus.PENDING,
            case_input=case_input,
            input_data=input_data,
            output_data={},
            errors=[],
            metadata={"workflow_name": self.name}
        )
    
    async def _execute_tool(self, tool_name: str, state: BusinessCaseAgentState, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with Business Case-specific input building."""
        
        if tool_name == "gather_case_inputs":
            return await self._execute_gather_inputs(state)
        
        elif tool_name == "assemble_document":
            return await self._execute_assemble_document(state)
        
        return await super()._execute_tool(tool_name, state, config)
    
    async def _execute_agent(self, node_config, state: BusinessCaseAgentState) -> Dict[str, Any]:
        """Execute agent node (sub-workflow)."""
        if node_config.id == "run_roi":
            return await self._execute_roi_subworkflow(state)
        
        return {"status": "agent_not_implemented"}
    
    async def _execute_llm(self, node_config, state: BusinessCaseAgentState) -> Dict[str, Any]:
        """Execute LLM node for section generation."""
        if node_config.id == "generate_narrative":
            return await self._execute_generate_sections(state)
        
        return {"status": "llm_not_implemented"}
    
    async def _execute_gather_inputs(self, state: BusinessCaseAgentState) -> Dict[str, Any]:
        """Gather all inputs needed for business case generation."""
        if not state.case_input:
            return {"error": "No business case input configured"}
        
        prospect_id = state.case_input.prospect_id
        
        # Fetch prospect data
        prospect_data = await self.tool_registry.execute(
            "get_prospect_data",
            {
                "prospect_id": prospect_id,
                "data_types": ["profile", "interactions", "opportunities"]
            }
        )
        
        # Fetch interaction history
        interactions = await self.tool_registry.execute(
            "fetch_interaction_history",
            {
                "prospect_id": prospect_id,
                "limit": 10
            }
        )
        
        # Score lead for additional context
        lead_score = await self.tool_registry.execute(
            "score_lead",
            {"prospect_id": prospect_id}
        )
        
        return {
            "prospect": prospect_data,
            "interactions": interactions,
            "lead_score": lead_score,
            "sections_requested": state.case_input.sections_requested,
            "output_format": state.case_input.output_format
        }
    
    async def _execute_roi_subworkflow(self, state: BusinessCaseAgentState) -> Dict[str, Any]:
        """Execute ROI calculation as sub-workflow."""
        if not state.case_input:
            return {"error": "No business case input configured"}
        
        prospect_id = state.case_input.prospect_id
        
        # Create ROI workflow state
        roi_input_data = {
            "prospect_id": prospect_id,
            "value_driver_ids": ["vd-001", "vd-002", "vd-003"],  # Default set
            "use_benchmarks": True
        }
        
        roi_initial_state = self.roi_workflow.create_initial_state(roi_input_data)
        
        # Run ROI workflow
        try:
            roi_result = await self.roi_workflow.run(roi_initial_state)
            
            return {
                "status": "completed",
                "roi_results": roi_result.output_data.get("aggregate", {}),
                "detailed_calculations": roi_result.calculation_results
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "roi_results": {}
            }
    
    async def _execute_generate_sections(self, state: BusinessCaseAgentState) -> Dict[str, Any]:
        """Generate all requested narrative sections."""
        if not state.case_input:
            return {"error": "No business case input configured", "sections": []}
        
        gathered = state.output_data.get("gather_inputs", {})
        roi_data = state.output_data.get("run_roi", {})
        
        prospect = gathered.get("prospect", {})
        profile = prospect.get("profile", {})
        roi_results = roi_data.get("roi_results", {})
        
        sections_generated: List[BusinessCaseSection] = []
        
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
                        "max_length": 500
                    }
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
                                {"label": "Investment", "value": roi_results.get("investment_required", 0)},
                                {"label": "Year 1 Value", "value": roi_results.get("total_annual_value", 0)},
                                {"label": "3-Year NPV", "value": roi_results.get("three_year_npv", 0)},
                            ],
                            "title": "ROI Summary",
                        }
                    )
                    charts.append(chart_result.get("chart_data", {}))
                
                section = BusinessCaseSection(
                    title=title,
                    content=section_result.get("content", ""),
                    charts=charts,
                    tables=[]
                )
                sections_generated.append(section)
                
            except Exception as e:
                # Add error section
                section = BusinessCaseSection(
                    title=title,
                    content=f"Error generating section: {str(e)}",
                    charts=[],
                    tables=[]
                )
                sections_generated.append(section)
        
        return {
            "sections": [s.model_dump() for s in sections_generated],
            "section_count": len(sections_generated)
        }
    
    async def _execute_assemble_document(self, state: BusinessCaseAgentState) -> Dict[str, Any]:
        """Assemble sections into final document."""
        if not state.case_input:
            return {"error": "No business case input configured"}
        
        sections_data = state.output_data.get("generate_narrative", {}).get("sections", [])
        
        if not sections_data:
            return {"error": "No sections generated"}
        
        # Prepare sections for assembly
        assembly_sections = []
        for s in sections_data:
            assembly_sections.append({
                "title": s.get("title", "Section"),
                "content": s.get("content", ""),
                "charts": s.get("charts", []),
                "tables": s.get("tables", [])
            })
        
        # Assemble document
        try:
            result = await self.tool_registry.execute(
                "assemble_document",
                {
                    "sections": assembly_sections,
                    "template": "business_case",
                    "output_format": state.case_input.output_format,
                    "branding": {
                        "company_name": state.case_input.custom_inputs.get("company_name", "Value Fabric"),
                        "date": state.case_input.custom_inputs.get("date", "2024")
                    }
                }
            )
            
            return {
                "document_bytes": result.get("document_bytes"),
                "document_url": result.get("document_url"),
                "page_count": result.get("page_count", len(assembly_sections)),
                "file_size_bytes": result.get("file_size_bytes", 0),
                "format": state.case_input.output_format
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "document_bytes": None,
                "document_url": None
            }
