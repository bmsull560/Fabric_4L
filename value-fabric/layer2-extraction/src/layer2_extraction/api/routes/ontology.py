"""Ontology routes for Layer 2 API."""

from fastapi import APIRouter, Query

from .. import main as handlers

router = APIRouter(prefix="/v1/ontology", tags=["ontology"])


@router.get("/entities")
async def list_entities(
    entity_type: str | None = Query(
        None,
        enum=["Capability", "UseCase", "Persona", "ValueDriver", "Feature"],
    ),
    limit: int = Query(100, ge=1, le=1000),
):
    return await handlers.list_entities(entity_type=entity_type, limit=limit)


@router.get("/relationships/{entity_id}")
async def get_relationships(entity_id: str):
    return await handlers.get_relationships(entity_id)
