"""LLM-based entity extraction using OpenAI Function Calling.

Stage 2 and 3 of the extraction pipeline: Extract entities and relationships
using structured LLM outputs with strict schema compliance.
"""

import json
from typing import Dict, List, Optional, Type, Any
from datetime import datetime

# OpenAI import with graceful fallback
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

from pydantic import BaseModel

from layer2_extraction.models import (
    Capability, UseCase, Persona, ValueDriver, Feature,
    Relationship, PredicateType, RoleType, ValueCategory
)


class LLMExtractionError(Exception):
    """Raised when LLM extraction fails or returns invalid data."""
    pass


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
        "required": ["name", "description", "confidence"]
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
        "required": ["name", "description", "confidence"]
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
        "required": ["role_type", "title", "department", "confidence"]
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
        "required": ["category", "name", "description", "unit", "confidence"]
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
        "required": ["name", "description", "confidence"]
    }
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", timeout: float = 60.0):
        """Initialize extractor with OpenAI client.
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: Model to use (gpt-4o, gpt-4o-mini, etc.)
            timeout: Timeout for API calls in seconds (default: 60.0)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Run: pip install openai")
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self.model = model
    
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
        tools = [{
            "type": "function",
            "function": {
                "name": "extract_capabilities",
                "description": "Extract product/technical capabilities from text. Only extract high-confidence capabilities.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "capabilities": {
                            "type": "array",
                            "items": self.CAPABILITY_SCHEMA
                        }
                    },
                    "required": ["capabilities"]
                }
            }
        }]
        
        prompt = f"""Extract all product/technical capabilities mentioned in this text.

Text:
{text}

Instructions:
- Only extract capabilities you're highly confident about (confidence >= {confidence_threshold})
- Include specific technical features when mentioned
- Focus on what the product/service CAN DO (capabilities), not benefits
- Return empty array if no clear capabilities are mentioned
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an enterprise ontology extractor. Be precise and conservative."},
                    {"role": "user", "content": prompt}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "extract_capabilities"}},
                temperature=0.0
            )
            
            tool_call = response.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            
            capabilities = []
            for cap_data in args.get("capabilities", []):
                if cap_data.get("confidence", 0) >= confidence_threshold:
                    cap = Capability(
                        name=cap_data["name"],
                        description=cap_data["description"],
                        technical_features=cap_data.get("technical_features", []),
                        api_endpoints=cap_data.get("api_endpoints", []),
                        integrations=cap_data.get("integrations", []),
                        confidence=cap_data["confidence"],
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
        tools = [{
            "type": "function",
            "function": {
                "name": "extract_use_cases",
                "description": "Extract business use cases from text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "use_cases": {
                            "type": "array",
                            "items": self.USECASE_SCHEMA
                        }
                    },
                    "required": ["use_cases"]
                }
            }
        }]
        
        prompt = f"""Extract all business use cases mentioned in this text.

Text:
{text}

Instructions:
- A use case is a specific business problem being solved
- Include workflow steps if described
- Note applicable industries
- Return empty array if no clear use cases are mentioned
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an enterprise ontology extractor. Be precise and conservative."},
                    {"role": "user", "content": prompt}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "extract_use_cases"}},
                temperature=0.0
            )
            
            tool_call = response.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            
            use_cases = []
            for uc_data in args.get("use_cases", []):
                if uc_data.get("confidence", 0) >= confidence_threshold:
                    uc = UseCase(
                        name=uc_data["name"],
                        description=uc_data["description"],
                        industry_context=uc_data.get("industry_context", []),
                        workflow_steps=uc_data.get("workflow_steps", []),
                        kpis=uc_data.get("kpis", []),
                        confidence=uc_data["confidence"],
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
        tools = [{
            "type": "function",
            "function": {
                "name": "extract_personas",
                "description": "Extract stakeholder personas from text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "personas": {
                            "type": "array",
                            "items": self.PERSONA_SCHEMA
                        }
                    },
                    "required": ["personas"]
                }
            }
        }]
        
        prompt = f"""Extract all stakeholder personas mentioned in this text.

Text:
{text}

Role Types:
- economic_buyer: Makes purchasing decisions (CFO, VP, Director)
- operational_user: Uses the product day-to-day (analyst, specialist)
- stakeholder: Influenced by outcomes but not direct user (auditor, customer)

Instructions:
- Include pain points and success metrics if mentioned
- Return empty array if no clear personas are mentioned
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an enterprise ontology extractor. Be precise and conservative."},
                    {"role": "user", "content": prompt}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "extract_personas"}},
                temperature=0.0
            )
            
            tool_call = response.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            
            personas = []
            for p_data in args.get("personas", []):
                if p_data.get("confidence", 0) >= confidence_threshold:
                    p = Persona(
                        role_type=RoleType(p_data["role_type"]),
                        title=p_data["title"],
                        department=p_data["department"],
                        pain_points=p_data.get("pain_points", []),
                        success_metrics=p_data.get("success_metrics", []),
                        confidence=p_data["confidence"],
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
        tools = [{
            "type": "function",
            "function": {
                "name": "extract_value_drivers",
                "description": "Extract quantifiable business value drivers from text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "value_drivers": {
                            "type": "array",
                            "items": self.VALUEDRIVER_SCHEMA
                        }
                    },
                    "required": ["value_drivers"]
                }
            }
        }]
        
        prompt = f"""Extract all quantifiable business value drivers mentioned in this text.

Text:
{text}

Categories:
- revenue: Increases revenue (up-sell, cross-sell, retention)
- cost: Reduces costs (automation, efficiency)
- risk: Reduces risk (compliance, security)
- capital: Optimizes capital (cash flow, inventory)

Instructions:
- Look for specific metrics and formulas
- Include time-to-value if mentioned
- Return empty array if no clear value drivers are mentioned
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an enterprise ontology extractor. Be precise and conservative."},
                    {"role": "user", "content": prompt}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "extract_value_drivers"}},
                temperature=0.0
            )
            
            tool_call = response.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            
            value_drivers = []
            for vd_data in args.get("value_drivers", []):
                if vd_data.get("confidence", 0) >= confidence_threshold:
                    vd = ValueDriver(
                        category=ValueCategory(vd_data["category"]),
                        name=vd_data["name"],
                        description=vd_data["description"],
                        metrics=vd_data.get("metrics", []),
                        formula_string=vd_data.get("formula_string"),
                        unit=vd_data["unit"],
                        time_to_value=vd_data.get("time_to_value"),
                        confidence=vd_data["confidence"],
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
        tools = [{
            "type": "function",
            "function": {
                "name": "extract_features",
                "description": "Extract product features from text. Features are concrete product functionality that implements capabilities.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "features": {
                            "type": "array",
                            "items": self.FEATURE_SCHEMA
                        }
                    },
                    "required": ["features"]
                }
            }
        }]
        
        prompt = f"""Extract all product features mentioned in this text.

Text:
{text}

Instructions:
- A feature is a concrete product functionality (e.g., "Dashboard Widget", "API Endpoint")
- Features implement capabilities - they are the "how" to capability's "what"
- Note the implementation status if mentioned (planned, beta, generally available, deprecated)
- Return empty array if no clear features are mentioned
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an enterprise ontology extractor. Be precise and conservative."},
                    {"role": "user", "content": prompt}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "extract_features"}},
                temperature=0.0
            )
            
            tool_call = response.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            
            features = []
            for f_data in args.get("features", []):
                if f_data.get("confidence", 0) >= confidence_threshold:
                    f = Feature(
                        name=f_data["name"],
                        description=f_data["description"],
                        parent_capability_id=f_data.get("parent_capability_id"),
                        technical_spec=f_data.get("technical_spec"),
                        implementation_status=f_data.get("implementation_status", "ga"),
                        confidence=f_data["confidence"],
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
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Run: pip install openai")
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self.model = model
    
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
        # Build entity index for reference
        entity_list = []
        for entity_type, entity_items in entities.items():
            for entity in entity_items:
                entity_list.append({
                    "id": entity.id,
                    "type": entity_type,
                    "name": getattr(entity, "name", getattr(entity, "title", "Unknown"))
                })
        
        if len(entity_list) < 2:
            return []
        
        tools = [{
            "type": "function",
            "function": {
                "name": "extract_relationships",
                "description": "Extract relationships between entities. Only create relationships if explicit evidence exists in text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "relationships": {
                            "type": "array",
                            "items": {
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
                                "required": ["source_id", "predicate", "target_id", "evidence_text", "confidence"]
                            }
                        }
                    },
                    "required": ["relationships"]
                }
            }
        }]
        
        prompt = f"""Given the text and the list of extracted entities, identify relationships between them.

Text:
{text}

Entities:
{json.dumps(entity_list, indent=2)}

Relationship Types:
- enables: Capability → UseCase (capability makes use case possible)
- requires: UseCase → Capability (use case needs capability)
- benefits: UseCase → Persona (use case helps persona)
- drives: Persona → ValueDriver (persona cares about value)
- contributes_to: Capability → ValueDriver (capability creates value)
- depends_on: Capability → Capability (capability needs another)
- alternative_to: Capability → Capability (alternative solution)
- capability_subtype_of: Capability → Capability (specialization hierarchy)
- capability_requires_capability: Capability → Capability (dependency chain)
- semantically_equivalent: Entity → Entity (same concept, different names)
- implements: Feature → Capability (feature delivers capability)
- delivers: UseCase → ValueDriver (use case produces value outcome)
- involves: UseCase → Persona (use case includes persona participation)

Instructions:
- ONLY create relationships if EXPLICIT evidence exists in the text
- Include direct quote as evidence_text
- Be conservative: low confidence if evidence is indirect
- Return empty array if no clear relationships exist
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an enterprise ontology extractor. Be conservative - only extract relationships with explicit evidence."},
                    {"role": "user", "content": prompt}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "extract_relationships"}},
                temperature=0.0
            )
            
            tool_call = response.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            
            relationships = []
            for rel_data in args.get("relationships", []):
                if rel_data.get("confidence", 0) >= confidence_threshold:
                    rel = Relationship(
                        source_id=rel_data["source_id"],
                        predicate=PredicateType(rel_data["predicate"]),
                        target_id=rel_data["target_id"],
                        confidence=rel_data["confidence"],
                        evidence_text=rel_data["evidence_text"],
                        source_url=source_url,
                        impact_level=rel_data.get("impact_level"),
                        extraction_job_id=extraction_job_id
                    )
                    relationships.append(rel)
            
            return relationships
            
        except Exception as e:
            raise LLMExtractionError(f"Failed to extract relationships: {e}")
