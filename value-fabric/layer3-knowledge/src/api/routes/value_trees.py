"""Value Tree API routes.

Provides endpoints for traversing and retrieving the 4-layer value tree:
- Capability -> UseCase -> Persona -> ValueDriver
"""

from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dependencies import get_graph_rag, get_app_state, AppState

router = APIRouter()


class ValueTreeNode(BaseModel):
    """Node in the value tree."""
    id: str = Field(..., description="Entity ID")
    label: str = Field(..., description="Display name")
    type: str = Field(..., description="Entity type (Capability, UseCase, Persona, ValueDriver)")
    layer: int = Field(..., ge=1, le=4, description="Layer in value tree (1=Capability, 4=ValueDriver)")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    properties: Dict[str, Any] = Field(default_factory=dict)


class ValueTreeEdge(BaseModel):
    """Edge connecting nodes in the value tree."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Relationship type (ENABLES, BENEFITS, DRIVES)")
    weight: float = Field(default=1.0, ge=0.0)


class ValueTreeStats(BaseModel):
    """Statistics for the value tree."""
    total_nodes: int = Field(..., ge=0)
    total_edges: int = Field(..., ge=0)
    by_layer: Dict[str, int] = Field(default_factory=dict)
    max_depth: int = Field(default=0)


class ValueTreeResponse(BaseModel):
    """Complete value tree response."""
    root_entity_id: str = Field(..., description="ID of the starting entity")
    direction: Literal["upward", "downward"] = Field(..., description="Traversal direction")
    nodes: List[ValueTreeNode] = Field(..., description="All nodes in the tree")
    edges: List[ValueTreeEdge] = Field(..., description="All edges in the tree")
    paths: List[Dict[str, Any]] = Field(default_factory=list, description="Value tree paths")
    stats: ValueTreeStats = Field(..., description="Tree statistics")


@router.get(
    "/value-trees/{entity_id}",
    response_model=ValueTreeResponse,
    tags=["Value Trees"],
    summary="Get Value Tree",
    description="Returns the resolved value tree starting from the specified entity.",
    responses={
        200: {
            "description": "Value tree retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "root_entity_id": "cap-1",
                        "direction": "upward",
                        "nodes": [
                            {"id": "cap-1", "label": "CRM Integration", "type": "Capability", "layer": 1},
                            {"id": "uc-1", "label": "Pipeline Forecast", "type": "UseCase", "layer": 2},
                        ],
                        "edges": [
                            {"source": "cap-1", "target": "uc-1", "type": "ENABLES"}
                        ],
                        "stats": {
                            "total_nodes": 15,
                            "total_edges": 14,
                            "by_layer": {"1": 3, "2": 5, "3": 4, "4": 3}
                        }
                    }
                }
            }
        },
        404: {"description": "Entity not found"},
    }
)
async def get_value_tree(
    entity_id: str,
    direction: Literal["upward", "downward"] = "upward",
    max_depth: int = 4,
    app_state: AppState = Depends(get_app_state),
) -> ValueTreeResponse:
    """Get the value tree starting from a specific entity.

    - **entity_id**: ID of the starting entity
    - **direction**: upward (Capability -> ValueDriver) or downward (ValueDriver -> Capability)
    - **max_depth**: Maximum traversal depth (1-4)
    """
    try:
        neo4j = app_state.neo4j_manager
        if not neo4j:
            raise HTTPException(status_code=503, detail="Neo4j not available")

        # Clamp depth
        max_depth = max(1, min(max_depth, 4))

        # Verify entity exists
        root_query = """
        MATCH (n {id: $entity_id})
        RETURN n.id as id, n.name as label, n.type as type, n.confidence as confidence
        """
        root_result = await neo4j.execute_query(root_query, {"entity_id": entity_id})
        if not root_result:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        root = root_result[0]
        root_type = root.get("type", "Unknown")

        # Determine layer for root
        layer_map = {"Capability": 1, "UseCase": 2, "Persona": 3, "ValueDriver": 4}
        root_layer = layer_map.get(root_type, 1)

        # Build traversal query based on direction
        if direction == "upward":
            # Traverse: Capability -(ENABLES)-> UseCase -(BENEFITS)-> Persona -(DRIVES)-> ValueDriver
            path_query = """
            MATCH path = (start {id: $entity_id})-[:ENABLES|BENEFITS|DRIVES*1..$max_depth]->(target)
            WHERE target.id IS NOT NULL
            RETURN start, target, relationships(path) as rels, nodes(path) as path_nodes,
                   length(path) as path_length
            """
        else:
            # Downward: ValueDriver <-(DRIVES)- Persona <-(BENEFITS)- UseCase <-(ENABLES)- Capability
            path_query = """
            MATCH path = (start {id: $entity_id})<-[:ENABLES|BENEFITS|DRIVES*1..$max_depth]-(target)
            WHERE target.id IS NOT NULL
            RETURN start, target, relationships(path) as rels, nodes(path) as path_nodes,
                   length(path) as path_length
            """

        path_result = await neo4j.execute_query(
            path_query,
            {"entity_id": entity_id, "max_depth": max_depth}
        )

        # Collect nodes and edges
        nodes_map: Dict[str, ValueTreeNode] = {}
        edges_map: Dict[str, ValueTreeEdge] = {}
        by_layer: Dict[str, int] = {}

        # Add root node
        nodes_map[entity_id] = ValueTreeNode(
            id=entity_id,
            label=root.get("label") or entity_id,
            type=root_type,
            layer=root_layer,
            confidence=root.get("confidence") or 0.8,
            properties={"is_root": True}
        )
        by_layer[str(root_layer)] = by_layer.get(str(root_layer), 0) + 1

        paths = []
        max_path_length = 0

        for r in path_result:
            path_nodes_data = r.get("path_nodes", [])
            rels = r.get("rels", [])
            path_length = r.get("path_length", 0)
            max_path_length = max(max_path_length, path_length)

            # Process nodes in path
            for i, node_data in enumerate(path_nodes_data):
                if not node_data or not node_data.get("id"):
                    continue

                node_id = node_data.get("id")
                node_type = node_data.get("type", "Unknown")
                node_layer = layer_map.get(node_type, 1)

                if node_id not in nodes_map:
                    by_layer[str(node_layer)] = by_layer.get(str(node_layer), 0) + 1
                    nodes_map[node_id] = ValueTreeNode(
                        id=node_id,
                        label=node_data.get("name") or node_id,
                        type=node_type,
                        layer=node_layer,
                        confidence=node_data.get("confidence") or 0.8,
                        properties={}
                    )

            # Process relationships
            for rel in rels:
                start_id = rel.get("start_node", {}).get("id")
                end_id = rel.get("end_node", {}).get("id")
                rel_type = rel.get("type", "RELATED_TO")

                if start_id and end_id:
                    edge_key = f"{start_id}-{end_id}-{rel_type}"
                    if edge_key not in edges_map:
                        edges_map[edge_key] = ValueTreeEdge(
                            source=start_id,
                            target=end_id,
                            type=rel_type,
                            weight=rel.get("weight", 1.0)
                        )

            # Build path structure
            if path_length > 0:
                paths.append({
                    "length": path_length,
                    "nodes": [n.get("id") for n in path_nodes_data if n],
                })

        nodes = list(nodes_map.values())
        edges = list(edges_map.values())

        stats = ValueTreeStats(
            total_nodes=len(nodes),
            total_edges=len(edges),
            by_layer=by_layer,
            max_depth=max_path_length
        )

        return ValueTreeResponse(
            root_entity_id=entity_id,
            direction=direction,
            nodes=nodes,
            edges=edges,
            paths=paths,
            stats=stats
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve value tree: {str(e)}")


@router.get(
    "/value-trees/{entity_id}/paths",
    response_model=List[Dict[str, Any]],
    tags=["Value Trees"],
    summary="Get Value Tree Paths",
    description="Returns all paths from the entity to value drivers (upward) or capabilities (downward).",
)
async def get_value_tree_paths(
    entity_id: str,
    direction: Literal["upward", "downward"] = "upward",
    max_depth: int = 4,
    app_state: AppState = Depends(get_app_state),
) -> List[Dict[str, Any]]:
    """Get all value tree paths from a starting entity."""
    try:
        neo4j = app_state.neo4j_manager
        if not neo4j:
            raise HTTPException(status_code=503, detail="Neo4j not available")

        max_depth = max(1, min(max_depth, 4))

        if direction == "upward":
            query = """
            MATCH path = (start {id: $entity_id})-[:ENABLES|BENEFITS|DRIVES*1..$max_depth]->(target:ValueDriver)
            RETURN [node in nodes(path) | {id: node.id, name: node.name, type: node.type}] as path_nodes,
                   length(path) as path_length
            """
        else:
            query = """
            MATCH path = (start {id: $entity_id})<-[:ENABLES|BENEFITS|DRIVES*1..$max_depth]-(target:Capability)
            RETURN [node in nodes(path) | {id: node.id, name: node.name, type: node.type}] as path_nodes,
                   length(path) as path_length
            """

        result = await neo4j.execute_query(query, {"entity_id": entity_id, "max_depth": max_depth})

        paths = []
        for r in result:
            paths.append({
                "nodes": r.get("path_nodes", []),
                "length": r.get("path_length", 0),
            })

        return paths

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve paths: {str(e)}")
