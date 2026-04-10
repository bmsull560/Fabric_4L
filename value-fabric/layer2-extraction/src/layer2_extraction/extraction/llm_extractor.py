"""LLM-based entity extraction using OpenAI Function Calling.

Stage 2 and 3 of the extraction pipeline: Extract entities and relationships
using structured LLM outputs with strict schema compliance.
"""

import json
import math
from typing import Dict, List, Optional, Any

from pydantic import BaseModel

from layer2_extraction.models import (
    Capability, UseCase, Persona, ValueDriver, Feature,
    Relationship, PredicateType, RoleType, ValueCategory
)
from layer2_extraction.shared.llm_client import CostRecord, LLMClient

from .prompt_loader import render_entity_prompt, render_relationship_prompt


class LLMExtractionError(Exception):
    """Raised when LLM extraction fails or returns invalid data."""
    pass


def _logprob_confidence_from_response(response: Any) -> Optional[float]:
    choices = getattr(response, "choices", None)
    if not choices:
        return None

    first_choice = choices[0]
    logprobs = getattr(first_choice, "logprobs", None)
    content = getattr(logprobs, "content", None) if logprobs else None
    if not content:
        return None

    values = [getattr(token, "logprob", None) for token in content]
    valid_logprobs = [v for v in values if v is not None]
    if not valid_logprobs:
        return None

    avg_logprob = sum(valid_logprobs) / len(valid_logprobs)
    return max(0.0, min(1.0, math.exp(avg_logprob)))


def _effective_confidence(item_confidence: float, logprob_confidence: Optional[float]) -> float:
    item = max(0.0, min(1.0, item_confidence))
    if logprob_confidence is None:
        return item

    token_conf = max(0.0, min(1.0, logprob_confidence))
    return max(0.0, min(1.0, (0.7 * item) + (0.3 * token_conf)))


def _parse_tool_arguments(response: Any, method_name: str) -> Dict[str, Any]:
    try:
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            raise ValueError("No tool calls returned")
        return json.loads(tool_calls[0].function.arguments)
    except Exception as exc:
        raise LLMExtractionError(f"{method_name}: invalid function-call payload: {exc}") from exc


def _strict_array_tool(
    function_name: str,
    description: str,
    array_field_name: str,
    item_schema: Dict[str, Any],
) -> List[Dict[str, Any]]:
    return [{
        "type": "function",
        "function": {
            "name": function_name,
            "description": description,
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    array_field_name: {
                        "type": "array",
                        "items": item_schema,
                    }
                },
                "required": [array_field_name],
                "additionalProperties": False,
            },
        },
    }]


class EntityExtractor:
    """Extract entities from text using OpenAI Function Calling.
    
    Uses temperature 0.0 for deterministic extraction with strict
    schema validation via Pydantic models.
    """
    
    # Schema definitions for OpenAI function calling
    CAPABILITY_SCHEMA = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Capability name"},
            "description": {"type": "string", "description": "Detailed description"},
            "technical_features": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific technical features"
            },
            "api_endpoints": {
                "type": "array",
                "items": {"type": "string"},
                "description": "API endpoints if applicable"
            },
            "integrations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Supported integrations"
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Confidence 0.0-1.0"
            }
        },
        "required": ["name", "description", "confidence"],
        "additionalProperties": False,
    }
    
    USECASE_SCHEMA = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Use case name"},
            "description": {"type": "string", "description": "Detailed description"},
            "industry_context": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Applicable industries"
            },
            "workflow_steps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ordered workflow steps"
            },
            "kpis": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key performance indicators"
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
            }
        },
        "required": ["name", "description", "confidence"],
        "additionalProperties": False,
    }
    
    PERSONA_SCHEMA = {
        "type": "object",
        "properties": {
            "role_type": {
                "type": "string",
                "enum": ["economic_buyer", "operational_user", "stakeholder"],
                "description": "Role in buying process"
            },
            "title": {"type": "string", "description": "Job title"},
            "department": {"type": "string", "description": "Department/organization"},
            "pain_points": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Problems this persona faces"
            },
            "success_metrics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "How they measure success"
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
            }
        },
        "required": ["role_type", "title", "department", "confidence"],
        "additionalProperties": False,
    }
    
    VALUEDRIVER_SCHEMA = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["revenue", "cost", "risk", "capital"],
                "description": "Type of value driver"
            },
            "name": {"type": "string", "description": "Value driver name"},
            "description": {"type": "string", "description": "Detailed description"},
            "metrics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific metrics"
            },
            "formula_string": {
                "type": "string",
                "description": "Mathematical formula for calculation (optional)"
            },
            "unit": {"type": "string", "description": "Unit of measurement"},
            "time_to_value": {
                "type": "string",
                "description": "Expected time to realize value"
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
            }
        },
        "required": ["category", "name", "description", "unit", "confidence"],
        "additionalProperties": False,
    }
    
    FEATURE_SCHEMA = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Feature name"},
            "description": {"type": "string", "description": "Detailed description"},
            "parent_capability_id": {
                "type": "string",
                "description": "UUID of parent capability (if mentioned)"
            },
            "technical_spec": {
                "type": "string",
                "description": "Technical specification details (optional)"
            },
            "implementation_status": {
                "type": "string",
                "enum": ["planned", "beta", "ga", "deprecated"],
                "description": "Current implementation status"
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
            }
        },
        "required": ["name", "description", "confidence"],
        "additionalProperties": False,
    }
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", timeout: float = 60.0):
        """Initialize extractor with OpenAI client.
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: Model to use (gpt-4o, gpt-4o-mini, etc.)
            timeout: Timeout for API calls in seconds (default: 60.0)
        """
        self.client = LLMClient(
            provider="openai",
            api_key=api_key,
            model=model,
            timeout=timeout,
            max_retries=3,
            cost_tracking_enabled=True,
        )
        self.model = self.client.model

    def get_cost_records(self) -> List[CostRecord]:
        """Return per-call cost records for this extractor."""
        return self.client.get_cost_records()

    def get_total_cost(self) -> float:
        """Return cumulative cost in USD for this extractor."""
        return self.client.get_total_cost()
    
    async def extract_entities(
        self,
        text: str,
        source_url: str,
        extraction_job_id: str,
        confidence_threshold: float = 0.8
    ) -> Dict[str, List[BaseModel]]:
        """Extract all entity types from text.
        
        Args:
            text: Text chunk to extract from
            source_url: Source URL for provenance
            extraction_job_id: Job ID for tracking
            confidence_threshold: Minimum confidence to include
            
        Returns:
            Dict with keys: capabilities, use_cases, personas, value_drivers, features
        """
        results = {
            "capabilities": [],
            "use_cases": [],
            "personas": [],
            "value_drivers": [],
            "features": []
        }
        
        # Extract each entity type
        results["capabilities"] = await self._extract_capabilities(
            text, source_url, extraction_job_id, confidence_threshold
        )
        results["use_cases"] = await self._extract_use_cases(
            text, source_url, extraction_job_id, confidence_threshold
        )
        results["personas"] = await self._extract_personas(
            text, source_url, extraction_job_id, confidence_threshold
        )
        results["value_drivers"] = await self._extract_value_drivers(
            text, source_url, extraction_job_id, confidence_threshold
        )
        results["features"] = await self._extract_features(
            text, source_url, extraction_job_id, confidence_threshold
        )
        
        return results
    
    async def _extract_capabilities(
        self,
        text: str,
        source_url: str,
        extraction_job_id: str,
        confidence_threshold: float
    ) -> List[Capability]:
        """Extract capabilities from text."""
        tools = _strict_array_tool(
            function_name="extract_capabilities",
            description="Extract product/technical capabilities from text. Only extract high-confidence capabilities.",
            array_field_name="capabilities",
            item_schema=self.CAPABILITY_SCHEMA,
        )

        prompt = render_entity_prompt(
            entity_type="capability",
            text=text,
            confidence_threshold=confidence_threshold,
        )
        
        try:
            response, _ = await self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an enterprise ontology extractor. Be precise and conservative."},
                    {"role": "user", "content": prompt}
                ],
                extraction_job_id=extraction_job_id,
                endpoint="extract_capabilities",
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "extract_capabilities"}},
                temperature=0.0,
                logprobs=True,
                top_logprobs=1,
            )

            args = _parse_tool_arguments(response, "extract_capabilities")
            logprob_confidence = _logprob_confidence_from_response(response)
            
            capabilities = []
            for cap_data in args.get("capabilities", []):
                calibrated_confidence = _effective_confidence(
                    float(cap_data.get("confidence", 0.0)),
                    logprob_confidence,
                )
                if calibrated_confidence >= confidence_threshold:
                    cap = Capability(
                        name=cap_data["name"],
                        description=cap_data["description"],
                        technical_features=cap_data.get("technical_features", []),
                        api_endpoints=cap_data.get("api_endpoints", []),
                        integrations=cap_data.get("integrations", []),
                        confidence=calibrated_confidence,
                        source_refs=[source_url],
                        extraction_job_id=extraction_job_id
                    )
                    capabilities.append(cap)
            
            return capabilities
            
        except Exception as e:
            raise LLMExtractionError(f"Failed to extract capabilities: {e}")
    
    async def _extract_use_cases(
        self,
        text: str,
        source_url: str,
        extraction_job_id: str,
        confidence_threshold: float
    ) -> List[UseCase]:
        """Extract use cases from text."""
        tools = _strict_array_tool(
            function_name="extract_use_cases",
            description="Extract business use cases from text.",
            array_field_name="use_cases",
            item_schema=self.USECASE_SCHEMA,
        )

        prompt = render_entity_prompt(
            entity_type="usecase",
            text=text,
            confidence_threshold=confidence_threshold,
        )
        
        try:
            response, _ = await self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an enterprise ontology extractor. Be precise and conservative."},
                    {"role": "user", "content": prompt}
                ],
                extraction_job_id=extraction_job_id,
                endpoint="extract_use_cases",
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "extract_use_cases"}},
                temperature=0.0,
                logprobs=True,
                top_logprobs=1,
            )

            args = _parse_tool_arguments(response, "extract_use_cases")
            logprob_confidence = _logprob_confidence_from_response(response)
            
            use_cases = []
            for uc_data in args.get("use_cases", []):
                calibrated_confidence = _effective_confidence(
                    float(uc_data.get("confidence", 0.0)),
                    logprob_confidence,
                )
                if calibrated_confidence >= confidence_threshold:
                    uc = UseCase(
                        name=uc_data["name"],
                        description=uc_data["description"],
                        industry_context=uc_data.get("industry_context", []),
                        workflow_steps=uc_data.get("workflow_steps", []),
                        kpis=uc_data.get("kpis", []),
                        confidence=calibrated_confidence,
                        extraction_job_id=extraction_job_id
                    )
                    use_cases.append(uc)
            
            return use_cases
            
        except Exception as e:
            raise LLMExtractionError(f"Failed to extract use cases: {e}")
    
    async def _extract_personas(
        self,
        text: str,
        source_url: str,
        extraction_job_id: str,
        confidence_threshold: float
    ) -> List[Persona]:
        """Extract personas from text."""
        tools = _strict_array_tool(
            function_name="extract_personas",
            description="Extract stakeholder personas from text.",
            array_field_name="personas",
            item_schema=self.PERSONA_SCHEMA,
        )

        prompt = render_entity_prompt(
            entity_type="persona",
            text=text,
            confidence_threshold=confidence_threshold,
        )
        
        try:
            response, _ = await self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an enterprise ontology extractor. Be precise and conservative."},
                    {"role": "user", "content": prompt}
                ],
                extraction_job_id=extraction_job_id,
                endpoint="extract_personas",
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "extract_personas"}},
                temperature=0.0,
                logprobs=True,
                top_logprobs=1,
            )

            args = _parse_tool_arguments(response, "extract_personas")
            logprob_confidence = _logprob_confidence_from_response(response)
            
            personas = []
            for p_data in args.get("personas", []):
                calibrated_confidence = _effective_confidence(
                    float(p_data.get("confidence", 0.0)),
                    logprob_confidence,
                )
                if calibrated_confidence >= confidence_threshold:
                    p = Persona(
                        role_type=RoleType(p_data["role_type"]),
                        title=p_data["title"],
                        department=p_data["department"],
                        pain_points=p_data.get("pain_points", []),
                        success_metrics=p_data.get("success_metrics", []),
                        confidence=calibrated_confidence,
                        extraction_job_id=extraction_job_id
                    )
                    personas.append(p)
            
            return personas
            
        except Exception as e:
            raise LLMExtractionError(f"Failed to extract personas: {e}")
    
    async def _extract_value_drivers(
        self,
        text: str,
        source_url: str,
        extraction_job_id: str,
        confidence_threshold: float
    ) -> List[ValueDriver]:
        """Extract value drivers from text."""
        tools = _strict_array_tool(
            function_name="extract_value_drivers",
            description="Extract quantifiable business value drivers from text.",
            array_field_name="value_drivers",
            item_schema=self.VALUEDRIVER_SCHEMA,
        )

        prompt = render_entity_prompt(
            entity_type="valuedriver",
            text=text,
            confidence_threshold=confidence_threshold,
        )
        
        try:
            response, _ = await self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an enterprise ontology extractor. Be precise and conservative."},
                    {"role": "user", "content": prompt}
                ],
                extraction_job_id=extraction_job_id,
                endpoint="extract_value_drivers",
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "extract_value_drivers"}},
                temperature=0.0,
                logprobs=True,
                top_logprobs=1,
            )

            args = _parse_tool_arguments(response, "extract_value_drivers")
            logprob_confidence = _logprob_confidence_from_response(response)
            
            value_drivers = []
            for vd_data in args.get("value_drivers", []):
                calibrated_confidence = _effective_confidence(
                    float(vd_data.get("confidence", 0.0)),
                    logprob_confidence,
                )
                if calibrated_confidence >= confidence_threshold:
                    vd = ValueDriver(
                        category=ValueCategory(vd_data["category"]),
                        name=vd_data["name"],
                        description=vd_data["description"],
                        metrics=vd_data.get("metrics", []),
                        formula_string=vd_data.get("formula_string"),
                        unit=vd_data["unit"],
                        time_to_value=vd_data.get("time_to_value"),
                        confidence=calibrated_confidence,
                        extraction_job_id=extraction_job_id
                    )
                    value_drivers.append(vd)
            
            return value_drivers
            
        except Exception as e:
            raise LLMExtractionError(f"Failed to extract value drivers: {e}")
    
    async def _extract_features(
        self,
        text: str,
        source_url: str,
        extraction_job_id: str,
        confidence_threshold: float
    ) -> List[Feature]:
        """Extract features from text."""
        tools = _strict_array_tool(
            function_name="extract_features",
            description="Extract product features from text. Features are concrete product functionality that implements capabilities.",
            array_field_name="features",
            item_schema=self.FEATURE_SCHEMA,
        )

        prompt = render_entity_prompt(
            entity_type="feature",
            text=text,
            confidence_threshold=confidence_threshold,
        )
        
        try:
            response, _ = await self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an enterprise ontology extractor. Be precise and conservative."},
                    {"role": "user", "content": prompt}
                ],
                extraction_job_id=extraction_job_id,
                endpoint="extract_features",
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "extract_features"}},
                temperature=0.0,
                logprobs=True,
                top_logprobs=1,
            )

            args = _parse_tool_arguments(response, "extract_features")
            logprob_confidence = _logprob_confidence_from_response(response)
            
            features = []
            for f_data in args.get("features", []):
                calibrated_confidence = _effective_confidence(
                    float(f_data.get("confidence", 0.0)),
                    logprob_confidence,
                )
                if calibrated_confidence >= confidence_threshold:
                    f = Feature(
                        name=f_data["name"],
                        description=f_data["description"],
                        parent_capability_id=f_data.get("parent_capability_id"),
                        technical_spec=f_data.get("technical_spec"),
                        implementation_status=f_data.get("implementation_status", "ga"),
                        confidence=calibrated_confidence,
                        source_refs=[source_url],
                        extraction_job_id=extraction_job_id
                    )
                    features.append(f)
            
            return features
            
        except Exception as e:
            raise LLMExtractionError(f"Failed to extract features: {e}")


class RelationshipExtractor:
    """Extract relationships between entities using LLM."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", timeout: float = 60.0):
        self.client = LLMClient(
            provider="openai",
            api_key=api_key,
            model=model,
            timeout=timeout,
            max_retries=3,
            cost_tracking_enabled=True,
        )
        self.model = self.client.model

    def get_cost_records(self) -> List[CostRecord]:
        """Return per-call cost records for this extractor."""
        return self.client.get_cost_records()

    def get_total_cost(self) -> float:
        """Return cumulative cost in USD for this extractor."""
        return self.client.get_total_cost()
    
    async def extract_relationships(
        self,
        text: str,
        entities: Dict[str, List[BaseModel]],
        source_url: str,
        extraction_job_id: str,
        confidence_threshold: float = 0.75
    ) -> List[Relationship]:
        """Extract relationships between identified entities.
        
        Args:
            text: Original text
            entities: Dict of entity lists from entity extraction
            source_url: Source URL
            extraction_job_id: Job ID
            confidence_threshold: Minimum confidence
            
        Returns:
            List of relationships with evidence
        """
        total_entities = sum(len(entity_items) for entity_items in entities.values())
        if total_entities < 2:
            return []
        
        relationship_schema = {
            "type": "object",
            "properties": {
                "source_id": {"type": "string", "description": "Source entity ID"},
                "predicate": {
                    "type": "string",
                    "enum": [
                        "enables", "requires", "benefits", "drives", "contributes_to", "depends_on", "alternative_to",
                        "capability_subtype_of", "capability_requires_capability", "semantically_equivalent",
                        "implements", "delivers", "involves"
                    ],
                    "description": "Relationship type"
                },
                "target_id": {"type": "string", "description": "Target entity ID"},
                "evidence_text": {"type": "string", "description": "Direct quote from text supporting this relationship"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "impact_level": {"type": "string", "enum": ["high", "medium", "low"]}
            },
            "required": ["source_id", "predicate", "target_id", "evidence_text", "confidence"],
            "additionalProperties": False,
        }

        tools = _strict_array_tool(
            function_name="extract_relationships",
            description="Extract relationships between entities. Only create relationships if explicit evidence exists in text.",
            array_field_name="relationships",
            item_schema=relationship_schema,
        )

        prompt = render_relationship_prompt(text=text, entities=entities)
        
        try:
            response, _ = await self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an enterprise ontology extractor. Be conservative - only extract relationships with explicit evidence."},
                    {"role": "user", "content": prompt}
                ],
                extraction_job_id=extraction_job_id,
                endpoint="extract_relationships",
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "extract_relationships"}},
                temperature=0.0,
                logprobs=True,
                top_logprobs=1,
            )

            args = _parse_tool_arguments(response, "extract_relationships")
            logprob_confidence = _logprob_confidence_from_response(response)
            
            relationships = []
            for rel_data in args.get("relationships", []):
                calibrated_confidence = _effective_confidence(
                    float(rel_data.get("confidence", 0.0)),
                    logprob_confidence,
                )
                if calibrated_confidence >= confidence_threshold:
                    rel = Relationship(
                        source_id=rel_data["source_id"],
                        predicate=PredicateType(rel_data["predicate"]),
                        target_id=rel_data["target_id"],
                        confidence=calibrated_confidence,
                        evidence_text=rel_data["evidence_text"],
                        source_url=source_url,
                        impact_level=rel_data.get("impact_level"),
                        extraction_job_id=extraction_job_id
                    )
                    relationships.append(rel)
            
            return relationships
            
        except Exception as e:
            raise LLMExtractionError(f"Failed to extract relationships: {e}")
