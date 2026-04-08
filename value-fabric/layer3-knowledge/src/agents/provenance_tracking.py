"""Provenance Tracking Agent.

Implements PROV-O lineage tracking with RDF-star annotations.
"""

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from neo4j import AsyncDriver

from .base import AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class PROVEntityType(Enum):
    """PROV-O entity types."""
    DOCUMENT = "prov:Entity:Document"
    SEGMENT = "prov:Entity:Segment"
    PAIN_POINT = "prov:Entity:PainPoint"
    VALUE_NODE = "prov:Entity:ValueNode"
    CALCULATION = "prov:Entity:Calculation"
    NARRATIVE = "prov:Entity:Narrative"
    ACCOUNT_PLAN = "prov:Entity:AccountPlan"
    FORMULA = "prov:Entity:Formula"


class PROVActivityType(Enum):
    """PROV-O activity types."""
    DOCUMENT_INGESTION = "prov:Activity:DocumentIngestion"
    EXTRACTION = "prov:Activity:Extraction"
    PROJECTION = "prov:Activity:Projection"
    TRAVERSAL = "prov:Activity:Traversal"
    CALCULATION = "prov:Activity:Calculation"
    SYNTHESIS = "prov:Activity:Synthesis"
    PLAN_GENERATION = "prov:Activity:PlanGeneration"


class PROVAgentType(Enum):
    """PROV-O agent types."""
    LLM_MODEL = "prov:Agent:LLMModel"
    AI_AGENT = "prov:Agent:AIAgent"
    USER = "prov:Agent:User"
    SYSTEM = "prov:Agent:System"
    EXTERNAL_SERVICE = "prov:Agent:ExternalService"


@dataclass
class RDFStarAnnotation:
    """RDF-star annotation for an edge."""
    annotation_id: str
    subject: str
    predicate: str
    object: str
    annotations: Dict[str, Any]
    created_at: datetime


@dataclass
class DecisionStep:
    """Single step in a decision trace."""
    step_id: str
    step_type: str
    step_number: int
    timestamp: datetime
    description: str
    input_refs: List[str]
    output_refs: List[str]
    agent_id: Optional[str]
    llm_model: Optional[str]
    confidence: Optional[float]
    reasoning: Optional[str]
    supporting_evidence: List[Dict[str, Any]]
    alternatives_considered: List[Dict[str, Any]]


@dataclass
class DecisionTrace:
    """Complete decision trace for an AI-generated output."""
    trace_id: str
    workflow_id: str
    workflow_instance_id: str
    output_type: str
    output_id: str
    created_at: datetime
    completed_at: Optional[datetime]
    steps: List[DecisionStep]


class ProvenanceTrackingAgent(BaseAgent):
    """Agent for provenance tracking and lineage recording.
    
    Capabilities:
    - prov_o_generation: Generate PROV-O compliant provenance
    - rdf_star_annotation: Annotate edges with execution metadata
    - lineage_tracking: Track data lineage through workflows
    - decision_trace_construction: Build decision traces for AI outputs
    
    Storage backend: triple_store (Neo4j with RDF-star support)
    """
    
    # PROV-O Namespaces
    PROV_NAMESPACES = {
        'prov': 'http://www.w3.org/ns/prov#',
        'vf': 'http://valuefabric.io/prov/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'xsd': 'http://www.w3.org/2001/XMLSchema#',
        'rdf-star': 'http://www.w3.org/ns/rdf-star#',
    }
    
    def __init__(self, driver: Optional[AsyncDriver] = None):
        """Initialize provenance tracking agent.
        
        Args:
            driver: Neo4j async driver for triple store
        """
        super().__init__("ProvenanceTrackingAgent")
        self._driver = driver
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute provenance tracking operation.
        
        Args:
            context: Must contain:
                - operation: 'record_entity', 'record_activity', 'record_derivation', 
                          'create_decision_trace', 'query_lineage'
                - workflow_id: ID of workflow
                - workflow_instance_id: ID of workflow instance
                
        Returns:
            AgentResult with provenance records
        """
        start_time = time.time()
        
        try:
            operation = context.get("operation", "record_entity")
            
            if operation == "record_entity":
                result = await self._record_entity(
                    entity_type=context.get("entity_type", "DOCUMENT"),
                    entity_id=context.get("entity_id"),
                    label=context.get("label"),
                    attributes=context.get("attributes", {}),
                )
            elif operation == "record_activity":
                result = await self._record_activity(
                    activity_type=context.get("activity_type", "EXTRACTION"),
                    activity_id=context.get("activity_id"),
                    label=context.get("label"),
                    attributes=context.get("attributes", {}),
                )
            elif operation == "record_derivation":
                result = await self._record_derivation(
                    derived_entity_id=context.get("derived_entity_id"),
                    source_entity_id=context.get("source_entity_id"),
                    derivation_type=context.get("derivation_type", "wasDerivedFrom"),
                )
            elif operation == "create_decision_trace":
                result = await self._create_decision_trace(
                    workflow_id=context.get("workflow_id"),
                    workflow_instance_id=context.get("workflow_instance_id"),
                    output_type=context.get("output_type"),
                    output_id=context.get("output_id"),
                    steps=context.get("steps", []),
                )
            elif operation == "query_lineage":
                result = await self._query_lineage(
                    entity_id=context.get("entity_id"),
                )
            else:
                return self._create_result(
                    status="failed",
                    output={},
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    errors=[f"Unknown operation: {operation}"],
                )
            
            return self._create_result(
                status="success",
                output=result,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
            
        except Exception as e:
            logger.error(f"Provenance tracking failed: {e}")
            return self._create_result(
                status="failed",
                output={},
                execution_time_ms=int((time.time() - start_time) * 1000),
                errors=[str(e)],
            )
    
    async def _record_entity(
        self,
        entity_type: str,
        entity_id: str,
        label: str,
        attributes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Record a PROV-O entity.
        
        Args:
            entity_type: Entity type from PROVEntityType
            entity_id: Unique entity ID
            label: Human-readable label
            attributes: Additional entity attributes
            
        Returns:
            Dict with recorded entity info
        """
        if not self._driver:
            return {"error": "No database driver"}
        
        full_entity_id = f"{self.PROV_NAMESPACES['vf']}entity/{entity_id}"
        
        query = """
        CREATE (e:PROVEntity:{{ entity_type }} {
            entity_id: $entity_id,
            full_id: $full_entity_id,
            label: $label,
            entity_type: $entity_type,
            generated_at: datetime(),
            attributes: $attributes
        })
        RETURN e.entity_id as id
        """
        
        async with self._driver.session() as session:
            result = await session.run(
                query,
                {
                    "entity_id": entity_id,
                    "full_entity_id": full_entity_id,
                    "label": label,
                    "entity_type": entity_type,
                    "attributes": attributes,
                },
            )
            record = await result.single()
            
        return {
            "entity_id": entity_id,
            "full_id": full_entity_id,
            "type": entity_type,
            "label": label,
            "recorded": record is not None,
        }
    
    async def _record_activity(
        self,
        activity_type: str,
        activity_id: str,
        label: str,
        attributes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Record a PROV-O activity.
        
        Args:
            activity_type: Activity type from PROVActivityType
            activity_id: Unique activity ID
            label: Human-readable label
            attributes: Additional activity attributes
            
        Returns:
            Dict with recorded activity info
        """
        if not self._driver:
            return {"error": "No database driver"}
        
        full_activity_id = f"{self.PROV_NAMESPACES['vf']}activity/{activity_id}"
        
        query = """
        CREATE (a:PROVActivity:{{ activity_type }} {
            activity_id: $activity_id,
            full_id: $full_activity_id,
            label: $label,
            activity_type: $activity_type,
            started_at: datetime(),
            attributes: $attributes
        })
        RETURN a.activity_id as id
        """
        
        async with self._driver.session() as session:
            result = await session.run(
                query,
                {
                    "activity_id": activity_id,
                    "full_activity_id": full_activity_id,
                    "label": label,
                    "activity_type": activity_type,
                    "attributes": attributes,
                },
            )
            record = await result.single()
        
        return {
            "activity_id": activity_id,
            "full_id": full_activity_id,
            "type": activity_type,
            "label": label,
            "recorded": record is not None,
        }
    
    async def _record_derivation(
        self,
        derived_entity_id: str,
        source_entity_id: str,
        derivation_type: str = "wasDerivedFrom",
    ) -> Dict[str, Any]:
        """Record a derivation relationship.
        
        Args:
            derived_entity_id: ID of derived entity
            source_entity_id: ID of source entity
            derivation_type: Type of derivation
            
        Returns:
            Dict with derivation record
        """
        if not self._driver:
            return {"error": "No database driver"}
        
        query = """
        MATCH (derived:PROVEntity {entity_id: $derived_id})
        MATCH (source:PROVEntity {entity_id: $source_id})
        CREATE (derived)-[r:wasDerivedFrom {
            derivation_type: $derivation_type,
            timestamp: datetime()
        }]->(source)
        RETURN r
        """
        
        async with self._driver.session() as session:
            result = await session.run(
                query,
                {
                    "derived_id": derived_entity_id,
                    "source_id": source_entity_id,
                    "derivation_type": derivation_type,
                },
            )
            record = await result.single()
        
        return {
            "derivation_type": derivation_type,
            "derived_entity": derived_entity_id,
            "source_entity": source_entity_id,
            "recorded": record is not None,
        }
    
    async def _create_decision_trace(
        self,
        workflow_id: str,
        workflow_instance_id: str,
        output_type: str,
        output_id: str,
        steps: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create a decision trace for AI-generated output.
        
        Args:
            workflow_id: Workflow definition ID
            workflow_instance_id: Workflow execution ID
            output_type: Type of output generated
            output_id: ID of generated output
            steps: List of decision steps
            
        Returns:
            Dict with decision trace
        """
        trace_id = f"trace-{uuid.uuid4().hex[:12]}"
        
        decision_trace = DecisionTrace(
            trace_id=trace_id,
            workflow_id=workflow_id,
            workflow_instance_id=workflow_instance_id,
            output_type=output_type,
            output_id=output_id,
            created_at=datetime.utcnow(),
            completed_at=None,
            steps=[],
        )
        
        # Convert step dicts to DecisionStep objects
        for i, step_data in enumerate(steps):
            step = DecisionStep(
                step_id=step_data.get("step_id", f"step-{i+1}"),
                step_type=step_data.get("step_type", "processing"),
                step_number=i + 1,
                timestamp=datetime.utcnow(),
                description=step_data.get("description", ""),
                input_refs=step_data.get("input_refs", []),
                output_refs=step_data.get("output_refs", []),
                agent_id=step_data.get("agent_id"),
                llm_model=step_data.get("llm_model"),
                confidence=step_data.get("confidence"),
                reasoning=step_data.get("reasoning"),
                supporting_evidence=step_data.get("supporting_evidence", []),
                alternatives_considered=step_data.get("alternatives_considered", []),
            )
            decision_trace.steps.append(step)
        
        decision_trace.completed_at = datetime.utcnow()
        
        # Store in database
        if self._driver:
            await self._store_decision_trace(decision_trace)
        
        return {
            "trace_id": trace_id,
            "workflow_id": workflow_id,
            "workflow_instance_id": workflow_instance_id,
            "output_type": output_type,
            "output_id": output_id,
            "step_count": len(decision_trace.steps),
            "steps": [
                {
                    "step_number": s.step_number,
                    "step_type": s.step_type,
                    "description": s.description,
                    "confidence": s.confidence,
                    "agent_id": s.agent_id,
                }
                for s in decision_trace.steps
            ],
            "created_at": decision_trace.created_at.isoformat(),
            "completed_at": decision_trace.completed_at.isoformat() if decision_trace.completed_at else None,
        }
    
    async def _store_decision_trace(self, trace: DecisionTrace) -> None:
        """Store decision trace in Neo4j.
        
        Args:
            trace: DecisionTrace to store
        """
        if not self._driver:
            return
        
        # Create trace node
        query = """
        CREATE (t:DecisionTrace {
            trace_id: $trace_id,
            workflow_id: $workflow_id,
            workflow_instance_id: $workflow_instance_id,
            output_type: $output_type,
            output_id: $output_id,
            created_at: datetime($created_at),
            completed_at: datetime($completed_at)
        })
        RETURN t
        """
        
        async with self._driver.session() as session:
            await session.run(
                query,
                {
                    "trace_id": trace.trace_id,
                    "workflow_id": trace.workflow_id,
                    "workflow_instance_id": trace.workflow_instance_id,
                    "output_type": trace.output_type,
                    "output_id": trace.output_id,
                    "created_at": trace.created_at.isoformat(),
                    "completed_at": trace.completed_at.isoformat() if trace.completed_at else None,
                },
            )
            
            # Create step nodes and link to trace
            for step in trace.steps:
                step_query = """
                MATCH (t:DecisionTrace {trace_id: $trace_id})
                CREATE (s:DecisionStep {
                    step_id: $step_id,
                    step_type: $step_type,
                    step_number: $step_number,
                    description: $description,
                    confidence: $confidence,
                    agent_id: $agent_id,
                    llm_model: $llm_model
                })
                CREATE (t)-[:HAS_STEP]->(s)
                """
                
                await session.run(
                    step_query,
                    {
                        "trace_id": trace.trace_id,
                        "step_id": step.step_id,
                        "step_type": step.step_type,
                        "step_number": step.step_number,
                        "description": step.description,
                        "confidence": step.confidence,
                        "agent_id": step.agent_id,
                        "llm_model": step.llm_model,
                    },
                )
    
    async def _query_lineage(self, entity_id: str) -> Dict[str, Any]:
        """Query lineage for an entity.
        
        Args:
            entity_id: Entity ID to query
            
        Returns:
            Dict with lineage information
        """
        if not self._driver:
            return {"lineage": [], "error": "No database driver"}
        
        # Query upstream lineage (what this entity was derived from)
        upstream_query = """
        MATCH path = (e:PROVEntity {entity_id: $entity_id})-[:wasDerivedFrom|wasGeneratedBy|used*1..10]->(source)
        RETURN [node in nodes(path) | {id: node.entity_id, type: node.entity_type, label: node.label}] as lineage
        """
        
        # Query downstream lineage (what was derived from this entity)
        downstream_query = """
        MATCH path = (e:PROVEntity {entity_id: $entity_id})<-[:wasDerivedFrom|wasGeneratedBy|used*1..10]-(derived)
        RETURN [node in nodes(path) | {id: node.entity_id, type: node.entity_type, label: node.label}] as lineage
        """
        
        upstream = []
        downstream = []
        
        async with self._driver.session() as session:
            # Get upstream
            result = await session.run(upstream_query, {"entity_id": entity_id})
            async for record in result:
                upstream.extend(record.get("lineage", []))
            
            # Get downstream
            result = await session.run(downstream_query, {"entity_id": entity_id})
            async for record in result:
                downstream.extend(record.get("lineage", []))
        
        return {
            "entity_id": entity_id,
            "upstream_lineage": upstream,
            "downstream_lineage": downstream,
            "full_lineage_depth": len(upstream) + len(downstream),
        }
    
    def create_rdf_star_annotation(
        self,
        subject: str,
        predicate: str,
        object: str,
        annotations: Dict[str, Any],
    ) -> RDFStarAnnotation:
        """Create RDF-star annotation for an edge.
        
        Args:
            subject: Edge subject
            predicate: Edge predicate
            object: Edge object
            annotations: Annotation attributes
            
        Returns:
            RDFStarAnnotation
        """
        return RDFStarAnnotation(
            annotation_id=f"anno-{uuid.uuid4().hex[:12]}",
            subject=subject,
            predicate=predicate,
            object=object,
            annotations=annotations,
            created_at=datetime.utcnow(),
        )
    
    def build_provenance_record(
        self,
        entity_type: str,
        entity_id: str,
        generated_by: str,
        used_entities: List[str],
        attributed_to: str,
    ) -> Dict[str, Any]:
        """Build complete provenance record.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            generated_by: Activity that generated it
            used_entities: Entities used in generation
            attributed_to: Agent responsible
            
        Returns:
            Dict with complete provenance
        """
        return {
            "entity": {
                "id": entity_id,
                "type": entity_type,
            },
            "generation": {
                "activity": generated_by,
                "timestamp": datetime.utcnow().isoformat(),
            },
            "usage": {
                "used_entities": used_entities,
            },
            "attribution": {
                "agent": attributed_to,
            },
            "rdf_triples": [
                (f"vf:{entity_id}", "prov:wasGeneratedBy", f"vf:{generated_by}"),
                (f"vf:{entity_id}", "prov:wasAttributedTo", f"vf:{attributed_to}"),
                *[(f"vf:{generated_by}", "prov:used", f"vf:{used}") for used in used_entities],
            ],
        }
