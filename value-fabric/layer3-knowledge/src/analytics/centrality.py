"""Centrality analysis for identifying key entities in the Knowledge Graph."""

import logging

from neo4j import AsyncDriver, AsyncGraphDatabase

from ..config import Settings, get_settings
from shared.models.typed_dict import TypedDictModel


class CentralityAnalyzer__fallback_centralityResult(TypedDictModel):
    algorithm: str
    note: str
    top_entities: Any
    total_ranked: Any

class CentralityAnalyzer_calculate_degree_centralityResult(TypedDictModel):
    algorithm: str
    top_entities: Any
    total_ranked: Any

class CentralityAnalyzer_get_value_tree_centralityResult(TypedDictModel):
    algorithm: str
    by_layer: dict[str, Any]
    key_connectors: Any

class CentralityAnalyzer_calculate_pagerankResult(TypedDictModel):
    algorithm: str
    top_entities: Any
    total_ranked: Any

class CentralityAnalyzer_calculate_betweennessResult(TypedDictModel):
    algorithm: str
    top_entities: Any
    total_ranked: Any

logger = logging.getLogger(__name__)


class CentralityAnalyzer:
    """Centrality analysis using Neo4j GDS.

    Identifies key entities in the knowledge graph using:
    - PageRank (overall importance)
    - Betweenness (bridge/connector importance)
    - Degree centrality (connectivity)
    - Eigenvector centrality (influence)
    """

    def __init__(
        self,
        driver: AsyncDriver | None = None,
        settings: Settings | None = None,
    ):
        """Initialize centrality analyzer.

        Args:
            driver: Neo4j async driver
            settings: Application settings
        """
        self.settings = settings or get_settings()
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

    async def calculate_pagerank(
        self,
        node_labels: list[str] | None = None,
        relationship_types: list[str] | None = None,
        top_k: int = 20,
    ) -> dict:
        """Calculate PageRank for all nodes.

        Args:
            node_labels: Filter by node labels
            relationship_types: Filter by relationship types
            top_k: Number of top results to return

        Returns:
            PageRank results
        """
        driver = await self._get_driver()

        async with driver.session(database=self.settings.neo4j_database) as session:
            try:
                # Check for GDS
                await session.run("RETURN gds.version() as version")
            except Exception:
                logger.warning("GDS not available, using fallback")
                return await self._fallback_centrality(
                    session, node_labels, "degree", top_k
                )

            graph_name = f"centrality_{self._random_id()}"

            try:
                # Project graph
                await self._project_graph(
                    session, graph_name, node_labels, relationship_types
                )

                # Calculate PageRank
                result = await session.run(
                    """
                    CALL gds.pageRank.stream($graph_name, {
                        maxIterations: 20,
                        dampingFactor: 0.85,
                        concurrency: 4
                    })
                    YIELD nodeId, score
                    RETURN gds.util.asNode(nodeId) as node, score
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    {"graph_name": graph_name, "limit": top_k},
                )

                rankings = []
                async for record in result:
                    node = record["node"]
                    rankings.append(
                        {
                            "id": node["id"],
                            "name": node.get("name", node.get("title", "Unknown")),
                            "type": list(node.labels)[0]
                            if hasattr(node, "labels")
                            else "Unknown",
                            "score": record["score"],
                        }
                    )

                return CentralityAnalyzer_calculate_pagerankResult.model_validate({
                    "algorithm": "pagerank",
                    "total_ranked": len(rankings),
                    "top_entities": rankings,
                })


            finally:
                await self._drop_graph(session, graph_name)

    async def calculate_betweenness(
        self,
        node_labels: list[str] | None = None,
        relationship_types: list[str] | None = None,
        top_k: int = 20,
    ) -> dict:
        """Calculate betweenness centrality.

        Identifies entities that act as bridges between different parts
        of the graph (important connectors).
        """
        driver = await self._get_driver()

        async with driver.session(database=self.settings.neo4j_database) as session:
            try:
                await session.run("RETURN gds.version() as version")
            except Exception:
                return await self._fallback_centrality(
                    session, node_labels, "betweenness", top_k
                )

            graph_name = f"centrality_{self._random_id()}"

            try:
                await self._project_graph(
                    session, graph_name, node_labels, relationship_types
                )

                result = await session.run(
                    """
                    CALL gds.betweenness.stream($graph_name, {
                        concurrency: 4
                    })
                    YIELD nodeId, score
                    RETURN gds.util.asNode(nodeId) as node, score
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    {"graph_name": graph_name, "limit": top_k},
                )

                rankings = []
                async for record in result:
                    node = record["node"]
                    rankings.append(
                        {
                            "id": node["id"],
                            "name": node.get("name", node.get("title", "Unknown")),
                            "type": list(node.labels)[0]
                            if hasattr(node, "labels")
                            else "Unknown",
                            "score": record["score"],
                        }
                    )

                return CentralityAnalyzer_calculate_betweennessResult.model_validate({
                    "algorithm": "betweenness",
                    "total_ranked": len(rankings),
                    "top_entities": rankings,
                })


            finally:
                await self._drop_graph(session, graph_name)

    async def calculate_degree_centrality(
        self,
        node_labels: list[str] | None = None,
        top_k: int = 20,
    ) -> dict:
        """Calculate degree centrality (simple connectivity count).

        Useful for finding hubs and highly connected entities.
        """
        driver = await self._get_driver()

        label_filter = ""
        if node_labels:
            labels = "|".join(node_labels)
            label_filter = f"WHERE n:{labels}"

        async with driver.session(database=self.settings.neo4j_database) as session:
            result = await session.run(
                f"""
                MATCH (n)
                {label_filter}
                OPTIONAL MATCH (n)-[r]-()
                WITH n, count(r) as degree
                RETURN n.id as id,
                       n.name as name,
                       labels(n)[0] as type,
                       degree
                ORDER BY degree DESC
                LIMIT $limit
                """,
                {"limit": top_k},
            )

            rankings = []
            async for record in result:
                rankings.append(
                    {
                        "id": record["id"],
                        "name": record["name"],
                        "type": record["type"],
                        "score": record["degree"],
                    }
                )

            return CentralityAnalyzer_calculate_degree_centralityResult.model_validate({
                "algorithm": "degree",
                "total_ranked": len(rankings),
                "top_entities": rankings,
            })


    async def get_value_tree_centrality(self) -> dict:
        """Analyze centrality within the 4-layer value tree.

        Returns key entities at each layer and cross-layer connectors.
        """
        driver = await self._get_driver()

        async with driver.session(database=self.settings.neo4j_database) as session:
            # Get most connected capabilities
            capabilities_result = await session.run(
                """
                MATCH (c:Capability)-[r:ENABLES]->(:UseCase)
                WITH c, count(r) as use_case_count
                RETURN c.id as id, c.name as name, use_case_count
                ORDER BY use_case_count DESC
                LIMIT 10
                """
            )
            top_capabilities = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "use_cases_enabled": r["use_case_count"],
                }
                async for r in capabilities_result
            ]

            # Get most beneficial use cases
            usecases_result = await session.run(
                """
                MATCH (uc:UseCase)-[r:BENEFITS]->(:Persona)
                WITH uc, count(r) as persona_count
                RETURN uc.id as id, uc.name as name, persona_count
                ORDER BY persona_count DESC
                LIMIT 10
                """
            )
            top_use_cases = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "personas_benefited": r["persona_count"],
                }
                async for r in usecases_result
            ]

            # Get most influential personas
            personas_result = await session.run(
                """
                MATCH (p:Persona)-[r:DRIVES]->(:ValueDriver)
                WITH p, count(r) as value_driver_count
                RETURN p.id as id, p.title as name, value_driver_count
                ORDER BY value_driver_count DESC
                LIMIT 10
                """
            )
            top_personas = [
                {
                    "id": r["id"],
                    "title": r["name"],
                    "value_drivers_driven": r["value_driver_count"],
                }
                async for r in personas_result
            ]

            # Get key connectors (entities bridging multiple layers)
            connectors_result = await session.run(
                """
                MATCH (n)
                WHERE (n)-[:ENABLES|:BENEFITS|:DRIVES]-()
                WITH n, 
                     count {(n)-[:ENABLES]->()} as enables_count,
                     count {(n)-[:BENEFITS]->()} as benefits_count,
                     count {(n)-[:DRIVES]->()} as drives_count
                WHERE (enables_count + benefits_count + drives_count) > 2
                RETURN n.id as id,
                       n.name as name,
                       labels(n)[0] as type,
                       enables_count, benefits_count, drives_count,
                       (enables_count + benefits_count + drives_count) as total
                ORDER BY total DESC
                LIMIT 10
                """
            )
            key_connectors = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "type": r["type"],
                    "outbound_connections": r["total"],
                }
                async for r in connectors_result
            ]

            return CentralityAnalyzer_get_value_tree_centralityResult.model_validate({
                "algorithm": "value_tree_analysis",
                "by_layer": {
                    "capabilities": top_capabilities,
                    "use_cases": top_use_cases,
                    "personas": top_personas,
                },
                "key_connectors": key_connectors,
            })


    async def _project_graph(
        self,
        session,
        graph_name: str,
        node_labels: list[str] | None,
        relationship_types: list[str] | None,
    ) -> None:
        """Project graph for GDS algorithms."""
        node_filter = node_labels or ["Capability", "UseCase", "Persona", "ValueDriver"]

        if not relationship_types:
            relationship_types = ["ENABLES", "BENEFITS", "DRIVES", "CONTRIBUTES_TO"]

        rel_filter = {rel: {"orientation": "UNDIRECTED"} for rel in relationship_types}

        await session.run(
            """
            CALL gds.graph.project(
                $graph_name,
                $node_filter,
                $rel_filter
            )
            """,
            {
                "graph_name": graph_name,
                "node_filter": node_filter,
                "rel_filter": rel_filter,
            },
        )

    async def _drop_graph(self, session, graph_name: str) -> None:
        """Drop GDS graph projection."""
        try:
            await session.run(
                "CALL gds.graph.drop($graph_name)",
                {"graph_name": graph_name},
            )
        except Exception as e:
            logger.debug(f"Could not drop graph: {e}")

    async def _fallback_centrality(
        self,
        session,
        node_labels: list[str] | None,
        metric: str,
        top_k: int,
    ) -> dict:
        """Fallback centrality using degree count."""
        label_filter = ""
        if node_labels:
            labels = "|".join(node_labels)
            label_filter = f"WHERE n:{labels}"

        result = await session.run(
            f"""
            MATCH (n)
            {label_filter}
            OPTIONAL MATCH (n)-[r]-()
            WITH n, count(r) as degree
            RETURN n.id as id,
                   n.name as name,
                   labels(n)[0] as type,
                   degree as score
            ORDER BY degree DESC
            LIMIT $limit
            """,
            {"limit": top_k},
        )

        rankings = []
        async for record in result:
            rankings.append(
                {
                    "id": record["id"],
                    "name": record["name"],
                    "type": record["type"],
                    "score": record["score"],
                }
            )

        return CentralityAnalyzer__fallback_centralityResult.model_validate({
            "algorithm": f"{metric}_fallback",
            "note": "Using degree centrality fallback - GDS not available",
            "total_ranked": len(rankings),
            "top_entities": rankings,
        })


    def _random_id(self) -> str:
        """Generate random ID."""
        import random
        import string

        return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
