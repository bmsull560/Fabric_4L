"""Neo4j RDF loader for ingesting Layer 2 extraction results."""

import logging
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from uuid import UUID

from neo4j import AsyncDriver, AsyncGraphDatabase
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

from ..config import Settings, get_settings
from ..schema.constraints import ENTITY_TYPES, RELATIONSHIP_TYPES

logger = logging.getLogger(__name__)

# Namespaces (aligned with value_fabric_ontology_schema.py spec)
VF = Namespace("http://valuefabric.io/ontology/")
PROV = Namespace("http://www.w3.org/ns/prov#")


class RDFLoadError(Exception):
    """Raised when RDF loading fails."""
    pass


class Neo4jLoader:
    """Load RDF triples into Neo4j Knowledge Graph."""

    def __init__(
        self,
        driver: Optional[AsyncDriver] = None,
        settings: Optional[Settings] = None,
        batch_size: int = 1000,
    ):
        """Initialize RDF loader.

        Args:
            driver: Neo4j async driver. If None, creates new connection.
            settings: Application settings. If None, loads from environment.
            batch_size: Number of triples to process in each batch.
        """
        self.settings = settings or get_settings()
        self.batch_size = batch_size
        self._driver = driver
        self._owned_driver = driver is None

    async def _get_driver(self) -> AsyncDriver:
        """Get or create Neo4j driver."""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=self.settings.neo4j_auth,
                max_connection_pool_size=self.settings.neo4j_max_pool_size,
            )
        return self._driver

    async def close(self) -> None:
        """Close Neo4j driver if owned."""
        if self._owned_driver and self._driver:
            await self._driver.close()
            self._driver = None

    async def load_rdf_graph(
        self,
        rdf_graph: Graph,
        source_id: Optional[str] = None,
        extraction_job_id: Optional[str] = None,
    ) -> dict:
        """Load an RDF graph into Neo4j.

        Args:
            rdf_graph: RDFLib Graph containing triples
            source_id: ID of the source document
            extraction_job_id: ID of the extraction job that generated this data

        Returns:
            Dictionary with load statistics
        """
        driver = await self._get_driver()
        stats = {
            "entities_loaded": 0,
            "relationships_loaded": 0,
            "triples_processed": 0,
            "errors": [],
            "start_time": datetime.utcnow().isoformat(),
        }

        async with driver.session(database=self.settings.neo4j_database) as session:
            # Extract and load entities
            entities = self._extract_entities_from_rdf(rdf_graph)
            for entity_type, entity_data in entities.items():
                loaded = await self._load_entities_batch(
                    session, entity_type, entity_data, source_id, extraction_job_id
                )
                stats["entities_loaded"] += loaded

            # Extract and load relationships
            relationships = self._extract_relationships_from_rdf(rdf_graph)
            loaded = await self._load_relationships_batch(
                session, relationships, source_id, extraction_job_id
            )
            stats["relationships_loaded"] += loaded

            stats["triples_processed"] = len(rdf_graph)
            stats["end_time"] = datetime.utcnow().isoformat()

        logger.info(
            f"Loaded {stats['entities_loaded']} entities and "
            f"{stats['relationships_loaded']} relationships from RDF"
        )

        return stats

    async def load_turtle_string(
        self,
        turtle_data: str,
        source_id: Optional[str] = None,
        extraction_job_id: Optional[str] = None,
    ) -> dict:
        """Load Turtle-formatted RDF string into Neo4j.

        Args:
            turtle_data: RDF data in Turtle format
            source_id: ID of the source document
            extraction_job_id: ID of the extraction job

        Returns:
            Dictionary with load statistics
        """
        try:
            g = Graph()
            g.parse(data=turtle_data, format="turtle")
            return await self.load_rdf_graph(g, source_id, extraction_job_id)
        except Exception as e:
            logger.error(f"Failed to parse Turtle data: {e}")
            raise RDFLoadError(f"Turtle parsing failed: {e}") from e

    def _extract_entities_from_rdf(self, graph: Graph) -> Dict[str, List[dict]]:
        """Extract entities grouped by type from RDF graph.

        Args:
            graph: RDFLib Graph

        Returns:
            Dictionary mapping entity type to list of entity data
        """
        entities: Dict[str, List[dict]] = {et: [] for et in ENTITY_TYPES}

        for entity_type in ENTITY_TYPES:
            type_uri = VF[entity_type]

            for subject in graph.subjects(RDF.type, type_uri):
                entity_data = {"id": str(subject), "uri": str(subject)}

                # Extract all properties for this entity
                for predicate, obj in graph.predicate_objects(subject):
                    pred_name = self._extract_property_name(predicate)

                    if isinstance(obj, Literal):
                        # Handle different literal types
                        if obj.datatype:
                            entity_data[pred_name] = self._convert_literal(obj)
                        else:
                            entity_data[pred_name] = str(obj)
                    elif isinstance(obj, URIRef):
                        entity_data[pred_name] = str(obj)

                entities[entity_type].append(entity_data)

        return entities

    def _extract_relationships_from_rdf(self, graph: Graph) -> List[dict]:
        """Extract relationships from RDF graph.

        Args:
            graph: RDFLib Graph

        Returns:
            List of relationship dictionaries
        """
        relationships = []

        for rel_type in RELATIONSHIP_TYPES:
            pred_uri = VF[rel_type]

            for subject, obj in graph.subject_objects(pred_uri):
                relationships.append({
                    "source_id": str(subject),
                    "target_id": str(obj),
                    "predicate": rel_type,
                })

        return relationships

    def _extract_property_name(self, uri: URIRef) -> str:
        """Extract property name from URI.

        Args:
            uri: Property URI

        Returns:
            Property name (local name)
        """
        uri_str = str(uri)
        if "#" in uri_str:
            return uri_str.split("#")[-1]
        return uri_str.split("/")[-1]

    def _convert_literal(self, literal: Literal) -> Any:
        """Convert RDF literal to Python value.

        Args:
            literal: RDFLib Literal

        Returns:
            Python value
        """
        if literal.datatype:
            datatype = str(literal.datatype)
            if "integer" in datatype or "int" in datatype:
                return int(literal)
            elif "float" in datatype or "double" in datatype:
                return float(literal)
            elif "boolean" in datatype:
                return bool(literal)
            elif "dateTime" in datatype:
                return str(literal)  # Keep as ISO string
        return str(literal)

    async def _load_entities_batch(
        self,
        session,
        entity_type: str,
        entities: List[dict],
        source_id: Optional[str],
        extraction_job_id: Optional[str],
    ) -> int:
        """Load a batch of entities into Neo4j.

        Args:
            session: Neo4j async session
            entity_type: Type of entities (e.g., Capability)
            entities: List of entity dictionaries
            source_id: Source document ID
            extraction_job_id: Extraction job ID

        Returns:
            Number of entities loaded
        """
        if not entities:
            return 0

        # Build dynamic Cypher query based on entity properties
        # Use MERGE to handle duplicates
        entity_data = {
            "entities": entities,
            "source_id": source_id,
            "extraction_job_id": extraction_job_id,
            "loaded_at": datetime.utcnow().isoformat(),
        }

        # Create entity nodes
        query = f"""
        UNWIND $entities as entity
        MERGE (n:{entity_type} {{id: entity.id}})
        SET n += apoc.map.removeKeys(entity, ['id'])
        SET n.source_id = $source_id
        SET n.extraction_job_id = $extraction_job_id
        SET n.loaded_at = datetime($loaded_at)
        RETURN count(n) as loaded
        """

        try:
            result = await session.run(query, entity_data)
            record = await result.single()
            return record["loaded"] if record else 0
        except Exception as e:
            logger.error(f"Failed to load {entity_type} entities: {e}")
            return 0

    async def _load_relationships_batch(
        self,
        session,
        relationships: List[dict],
        source_id: Optional[str],
        extraction_job_id: Optional[str],
    ) -> int:
        """Load relationships into Neo4j.

        Args:
            session: Neo4j async session
            relationships: List of relationship dictionaries
            source_id: Source document ID
            extraction_job_id: Extraction job ID

        Returns:
            Number of relationships loaded
        """
        if not relationships:
            return 0

        rel_data = {
            "relationships": relationships,
            "source_id": source_id,
            "extraction_job_id": extraction_job_id,
            "loaded_at": datetime.utcnow().isoformat(),
        }

        # Create relationships between existing nodes
        query = """
        UNWIND $relationships as rel
        MATCH (source {id: rel.source_id})
        MATCH (target {id: rel.target_id})
        WITH source, target, rel
        CALL apoc.merge.relationship(
            source,
            rel.predicate,
            {source_id: rel.source_id, target_id: rel.target_id},
            {
                source_id: $source_id,
                extraction_job_id: $extraction_job_id,
                loaded_at: datetime($loaded_at)
            },
            target
        ) YIELD rel as created_rel
        RETURN count(created_rel) as loaded
        """

        try:
            result = await session.run(query, rel_data)
            record = await result.single()
            return record["loaded"] if record else 0
        except Exception as e:
            logger.error(f"Failed to load relationships: {e}")
            return 0

    async def delete_by_source(self, source_id: str) -> dict:
        """Delete all entities and relationships from a specific source.

        Args:
            source_id: Source document ID to delete

        Returns:
            Dictionary with deletion statistics
        """
        driver = await self._get_driver()
        stats = {"entities_deleted": 0, "relationships_deleted": 0}

        async with driver.session(database=self.settings.neo4j_database) as session:
            # Delete relationships first
            rel_result = await session.run(
                """
                MATCH ()-[r]->()
                WHERE r.source_id = $source_id
                DELETE r
                RETURN count(r) as deleted
                """,
                {"source_id": source_id},
            )
            record = await rel_result.single()
            stats["relationships_deleted"] = record["deleted"] if record else 0

            # Delete entities
            entity_result = await session.run(
                """
                MATCH (n)
                WHERE n.source_id = $source_id
                DELETE n
                RETURN count(n) as deleted
                """,
                {"source_id": source_id},
            )
            record = await entity_result.single()
            stats["entities_deleted"] = record["deleted"] if record else 0

        logger.info(
            f"Deleted {stats['entities_deleted']} entities and "
            f"{stats['relationships_deleted']} relationships for source {source_id}"
        )

        return stats
