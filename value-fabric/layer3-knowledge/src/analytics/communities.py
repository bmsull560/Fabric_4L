"""Community detection algorithms for Knowledge Graph analysis."""

import logging
from typing import Any, Dict, List, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase

from ...config import Settings, get_settings

logger = logging.getLogger(__name__)


class CommunityDetector:
    """Community detection using Neo4j Graph Data Science (GDS).

    Detects communities of related entities (personas, use cases, capabilities)
    for pattern discovery and segmentation.
    """

    def __init__(
        self,
        driver: Optional[AsyncDriver] = None,
        settings: Optional[Settings] = None,
    ):
        """Initialize community detector.

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

    async def detect_louvain(
        self,
        node_labels: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
        min_community_size: int = 3,
        max_levels: int = 10,
    ) -> dict:
        """Detect communities using Louvain algorithm.

        Args:
            node_labels: Node labels to include (e.g., ["Persona", "UseCase"])
            relationship_types: Relationship types to follow
            min_community_size: Minimum size for a valid community
            max_levels: Maximum hierarchy levels

        Returns:
            Community detection results with statistics
        """
        driver = await self._get_driver()

        # Build graph projection
        node_filter = self._build_node_filter(node_labels)
        rel_filter = self._build_rel_filter(relationship_types)

        async with driver.session(database=self.settings.neo4j_database) as session:
            # Check if GDS is available
            try:
                await session.run("RETURN gds.version() as version")
            except Exception as e:
                logger.warning(f"GDS not available: {e}")
                return await self._fallback_community_detection(
                    session, node_labels, relationship_types, min_community_size
                )

            # Create in-memory graph projection
            graph_name = f"communities_{self._random_id()}"

            try:
                # Project graph
                await session.run(
                    f"""
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

                # Run Louvain
                result = await session.run(
                    """
                    CALL gds.louvain.stream($graph_name, {
                        maxLevels: $max_levels,
                        tolerance: 0.0001,
                        concurrency: 4
                    })
                    YIELD nodeId, communityId, intermediateCommunityIds
                    RETURN gds.util.asNode(nodeId) as node, communityId
                    """,
                    {"graph_name": graph_name, "max_levels": max_levels},
                )

                # Collect results
                communities: Dict[int, List[Dict]] = {}
                async for record in result:
                    node = record["node"]
                    community_id = record["communityId"]

                    if community_id not in communities:
                        communities[community_id] = []

                    communities[community_id].append({
                        "id": node["id"],
                        "name": node.get("name", node.get("title", "Unknown")),
                        "type": list(node.labels)[0] if hasattr(node, "labels") else "Unknown",
                    })

                # Filter small communities
                valid_communities = {
                    k: v for k, v in communities.items()
                    if len(v) >= min_community_size
                }

                return {
                    "algorithm": "louvain",
                    "total_communities": len(communities),
                    "valid_communities": len(valid_communities),
                    "total_nodes": sum(len(m) for m in communities.values()),
                    "communities": [
                        {
                            "id": cid,
                            "size": len(members),
                            "members": members,
                        }
                        for cid, members in valid_communities.items()
                    ],
                    "modularity": await self._calculate_modularity(
                        session, graph_name, valid_communities
                    ),
                }

            finally:
                # Cleanup graph projection
                try:
                    await session.run(
                        "CALL gds.graph.drop($graph_name)",
                        {"graph_name": graph_name},
                    )
                except Exception as e:
                    logger.debug(f"Could not drop graph projection: {e}")

    async def detect_leiden(
        self,
        node_labels: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
        min_community_size: int = 3,
    ) -> dict:
        """Detect communities using Leiden algorithm (higher quality than Louvain).

        Args:
            node_labels: Node labels to include
            relationship_types: Relationship types to follow
            min_community_size: Minimum community size

        Returns:
            Community detection results
        """
        driver = await self._get_driver()

        node_filter = self._build_node_filter(node_labels)
        rel_filter = self._build_rel_filter(relationship_types)

        async with driver.session(database=self.settings.neo4j_database) as session:
            try:
                await session.run("RETURN gds.version() as version")
            except Exception as e:
                logger.warning(f"GDS not available: {e}")
                return await self._fallback_community_detection(
                    session, node_labels, relationship_types, min_community_size
                )

            graph_name = f"communities_{self._random_id()}"

            try:
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

                # Run Leiden
                result = await session.run(
                    """
                    CALL gds.leiden.stream($graph_name, {
                        concurrency: 4
                    })
                    YIELD nodeId, communityId
                    RETURN gds.util.asNode(nodeId) as node, communityId
                    """,
                    {"graph_name": graph_name},
                )

                communities: Dict[int, List[Dict]] = {}
                async for record in result:
                    node = record["node"]
                    community_id = record["communityId"]

                    if community_id not in communities:
                        communities[community_id] = []

                    communities[community_id].append({
                        "id": node["id"],
                        "name": node.get("name", node.get("title", "Unknown")),
                        "type": list(node.labels)[0] if hasattr(node, "labels") else "Unknown",
                    })

                valid_communities = {
                    k: v for k, v in communities.items()
                    if len(v) >= min_community_size
                }

                return {
                    "algorithm": "leiden",
                    "total_communities": len(communities),
                    "valid_communities": len(valid_communities),
                    "total_nodes": sum(len(m) for m in communities.values()),
                    "communities": [
                        {
                            "id": cid,
                            "size": len(members),
                            "members": members,
                        }
                        for cid, members in valid_communities.items()
                    ],
                }

            finally:
                try:
                    await session.run(
                        "CALL gds.graph.drop($graph_name)",
                        {"graph_name": graph_name},
                    )
                except Exception as e:
                    logger.debug(f"Could not drop graph projection: {e}")

    async def detect_by_value_tree(self) -> dict:
        """Detect communities based on the 4-layer value tree structure.

        Groups entities that contribute to common value drivers.

        Returns:
            Value-tree based communities
        """
        driver = await self._get_driver()

        async with driver.session(database=self.settings.neo4j_database) as session:
            # Find all value drivers and their connected subgraphs
            result = await session.run(
                """
                MATCH (vd:ValueDriver)
                OPTIONAL MATCH path = (vd)<-[:DRIVES]-(:Persona)<-[:BENEFITS]-(:UseCase)<-[:ENABLES]-(:Capability)
                WITH vd, collect(path) as paths
                RETURN vd.id as value_driver_id,
                       vd.name as value_driver_name,
                       vd.category as category,
                       [path IN paths | [node IN nodes(path) | {
                           id: node.id,
                           name: node.name,
                           type: labels(node)[0]
                       }]] as connected_paths
                """
            )

            communities = []
            async for record in result:
                # Flatten paths into unique members
                all_members = []
                seen_ids = set()

                for path in record["connected_paths"]:
                    for node in path:
                        if node["id"] not in seen_ids:
                            seen_ids.add(node["id"])
                            all_members.append(node)

                if len(all_members) >= 2:  # At least some connection
                    communities.append({
                        "value_driver_id": record["value_driver_id"],
                        "value_driver_name": record["value_driver_name"],
                        "category": record["category"],
                        "size": len(all_members),
                        "members": all_members,
                    })

            return {
                "algorithm": "value_tree",
                "total_communities": len(communities),
                "communities": sorted(
                    communities,
                    key=lambda x: x["size"],
                    reverse=True
                ),
            }

    async def _fallback_community_detection(
        self,
        session,
        node_labels: Optional[List[str]],
        relationship_types: Optional[List[str]],
        min_size: int,
    ) -> dict:
        """Fallback using connected components when GDS unavailable."""
        label_filter = ""
        if node_labels:
            labels = "|".join(node_labels)
            label_filter = f"WHERE n:{labels}"

        rel_filter = ""
        if relationship_types:
            rels = "|".join(f"`{r}`" for r in relationship_types)
            rel_filter = f"-[r:{rels}]-"
        else:
            rel_filter = "--"

        result = await session.run(
            f"""
            MATCH (n){rel_filter}(m)
            {label_filter}
            WITH n, collect(m) as neighbors
            WHERE size(neighbors) >= $min_size - 1
            RETURN n.id as id, n.name as name, labels(n)[0] as type,
                   [x IN neighbors | x.id] as neighbor_ids
            """,
            {"min_size": min_size},
        )

        communities = []
        async for record in result:
            communities.append({
                "center_id": record["id"],
                "center_name": record["name"],
                "center_type": record["type"],
                "size": len(record["neighbor_ids"]) + 1,
                "members": [record["id"]] + record["neighbor_ids"],
            })

        return {
            "algorithm": "connected_components_fallback",
            "total_communities": len(communities),
            "communities": communities,
            "note": "Using fallback method - GDS not available",
        }

    async def _calculate_modularity(
        self,
        session,
        graph_name: str,
        communities: Dict[int, List],
    ) -> float:
        """Calculate modularity score for community quality."""
        try:
            result = await session.run(
                """
                CALL gds.modularity.stream($graph_name, {
                    communityProperty: 'communityId'
                })
                YIELD modularity
                RETURN avg(modularity) as avg_modularity
                """,
                {"graph_name": graph_name},
            )
            record = await result.single()
            return record["avg_modularity"] if record else 0.0
        except Exception as e:
            logger.debug(f"Could not calculate modularity: {e}")
            return 0.0

    def _build_node_filter(self, node_labels: Optional[List[str]]) -> Any:
        """Build node filter for GDS graph projection."""
        if not node_labels:
            return ["Capability", "UseCase", "Persona", "ValueDriver"]
        return node_labels

    def _build_rel_filter(self, relationship_types: Optional[List[str]]) -> Any:
        """Build relationship filter for GDS graph projection."""
        if not relationship_types:
            return {
                "ENABLES": {"orientation": "UNDIRECTED"},
                "BENEFITS": {"orientation": "UNDIRECTED"},
                "DRIVES": {"orientation": "UNDIRECTED"},
            }
        return {rel: {"orientation": "UNDIRECTED"} for rel in relationship_types}

    def _random_id(self) -> str:
        """Generate random ID for graph projection."""
        import random
        import string
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
