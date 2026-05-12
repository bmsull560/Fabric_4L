"""Typed structures for retrieval internals."""

from typing import Any, TypedDict


class SerializedRelationship(TypedDict, total=False):
    type: str
    relationship_type: str
    source: str
    target: str
    properties: dict[str, Any]
    hops: int


class ExpandedContextResult(TypedDict):
    entities: list[dict[str, Any]]
    relationships: list[SerializedRelationship]
    traversal_path: list[str]
    seed_count: int
    expanded_count: int


class EntityContextResult(TypedDict, total=False):
    center: dict[str, Any] | None
    neighbors: list[dict[str, Any]]
    relationships: list[SerializedRelationship]
    entity_count: int
    relationship_count: int


class ValueTreePath(TypedDict):
    nodes: list[dict[str, Any]]
    relationships: list[SerializedRelationship]


class TraverseValueTreeResult(TypedDict):
    start_entity_id: str
    direction: str
    paths: list[ValueTreePath]
    path_count: int
