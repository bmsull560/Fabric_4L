"""Ontology routes for Layer 2 API.

This module provides endpoints for both:
- Entity instance queries (existing entities in the graph)
- Schema management (ontology type definitions)
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from .. import main as handlers
from layer2_extraction.models.ontology import (
    OntologyProperty,
    OntologySchema,
    OntologyType,
    TypeRelationship,
    ValidationError,
    ValidationWarning,
)
from layer2_extraction.repositories.ontology_schema_repository import OntologySchemaRepository
from shared.models.typed_dict import TypedDictModel


class delete_ontology_typeResult(TypedDictModel):
    deleted: bool

class delete_type_relationshipResult(TypedDictModel):
    deleted: bool

class remove_type_propertyResult(TypedDictModel):
    removed: bool

router = APIRouter(prefix="/v1/ontology", tags=["ontology"])


# ============================================================================
# Entity Instance Queries (Existing Endpoints)
# ============================================================================

@router.get("/entities")
async def list_entities(
    entity_type: str | None = Query(
        None,
        enum=["Capability", "UseCase", "Persona", "ValueDriver", "Feature"],
    ),
    limit: int = Query(100, ge=1, le=1000),
):
    """List extracted entity instances from the knowledge graph."""
    return await handlers.list_entities(entity_type=entity_type, limit=limit)


@router.get("/relationships/{entity_id}")
async def get_relationships(entity_id: str):
    """Get relationships for a specific entity instance."""
    return await handlers.get_relationships(entity_id)


# ============================================================================
# Schema Management (New Endpoints)
# ============================================================================

# Request/Response Models

class CreateTypeRequest(BaseModel):
    name: str
    description: str
    parent_type_id: Optional[str] = None


class UpdateTypeRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CreateRelationshipRequest(BaseModel):
    source_type_id: str
    target_type_id: str
    relationship_type: str
    description: Optional[str] = None
    cardinality: str = "many_to_many"


class ValidateSchemaRequest(BaseModel):
    types: list[OntologyType]
    relationships: list[TypeRelationship]


class ValidateSchemaResponse(BaseModel):
    valid: bool
    errors: list[ValidationError]
    warnings: list[ValidationWarning]


class PublishSchemaRequest(BaseModel):
    version: str
    comment: Optional[str] = None


class PublishSchemaResponse(BaseModel):
    version: str
    published_at: str
    published_by: str


class ImportSchemaRequest(BaseModel):
    schema_data: str = Field(alias="schema_json")

    model_config = ConfigDict(populate_by_name=True)


# Dependency to get repository
async def get_repository() -> OntologySchemaRepository:
    return OntologySchemaRepository()


# Default values for development (should be overridden by auth middleware in production)
DEFAULT_TENANT_ID = "default"
DEFAULT_USER_ID = "system"


# CONTRACT §2.1 §2.3: Tenant context from GovernanceMiddleware, never direct header access
def get_tenant_id(request: Request) -> str:
    """Extract tenant ID from request context (set by GovernanceMiddleware).

    CONTRACT: All tenant identification flows through GovernanceMiddleware.
    Direct header access is prohibited per §2.1.
    """
    # Get from request state (set by GovernanceMiddleware via shared.identity)
    ctx = getattr(request.state, "governance_context", None)
    if ctx and ctx.tenant_id:
        return str(ctx.tenant_id)

    # Fail-safe: require explicit DEFAULT_TENANT_ID for dev/test only
    return DEFAULT_TENANT_ID


# CONTRACT §2.1: User context from GovernanceMiddleware
def get_user_id(request: Request) -> str:
    """Extract user ID from request context."""
    ctx = getattr(request.state, "governance_context", None)
    if ctx and ctx.user_id:
        return str(ctx.user_id)

    return DEFAULT_USER_ID


# Schema Endpoints

@router.get("/schema", response_model=OntologySchema)
async def get_ontology_schema(
    request: Request,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Get the complete ontology schema for the current tenant."""
    return await repo.get_schema()


@router.post("/schema/validate", response_model=ValidateSchemaResponse)
async def validate_ontology_schema(
    request: ValidateSchemaRequest,
):
    """Validate an ontology schema without saving it."""
    schema = OntologySchema(
        types=request.types,
        relationships=request.relationships,
    )
    is_valid, errors, warnings = schema.validate_schema()
    return ValidateSchemaResponse(valid=is_valid, errors=errors, warnings=warnings)


@router.post("/schema/publish", response_model=PublishSchemaResponse)
async def publish_ontology_schema(
    request: Request,
    body: PublishSchemaRequest,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Publish the current schema as a new version."""
    user_id = get_user_id(request)

    version = await repo.publish_schema(
        version=body.version,
        user_id=user_id,
        comment=body.comment,
    )

    return PublishSchemaResponse(
        version=version.version,
        published_at=version.published_at.isoformat(),
        published_by=version.published_by or user_id,
    )


@router.post("/schema/import", response_model=OntologySchema)
async def import_ontology_schema(
    request: Request,
    body: ImportSchemaRequest,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Import an ontology schema from JSON."""
    import json

    user_id = get_user_id(request)

    try:
        parsed_data = json.loads(body.schema_data)
        schema = OntologySchema(**parsed_data)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid schema: {e}")

    # Validate before importing
    is_valid, errors, _ = schema.validate_schema()
    if not is_valid:
        error_messages = ", ".join([e.message for e in errors if e.severity == "error"])
        raise HTTPException(status_code=400, detail=f"Schema validation failed: {error_messages}")

    imported = await repo.import_schema(schema, user_id)
    return imported


@router.get("/schema/export")
async def export_ontology_schema(
    request: Request,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Export the current ontology schema as JSON."""
    schema = await repo.get_schema()
    return schema


# Type Endpoints

@router.get("/schema/types", response_model=list[OntologyType])
async def list_ontology_types(
    request: Request,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """List all ontology types for the current tenant."""
    return await repo.get_all_types()


@router.get("/schema/types/{type_id}", response_model=OntologyType)
async def get_ontology_type(
    type_id: str,
    request: Request,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Get a specific ontology type by ID."""
    type_def = await repo.get_type_by_id(type_id)
    if not type_def:
        raise HTTPException(status_code=404, detail=f"Type {type_id} not found")
    return type_def


@router.post("/schema/types", response_model=OntologyType)
async def create_ontology_type(
    request: Request,
    body: CreateTypeRequest,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Create a new ontology type."""
    return await repo.create_type(
        name=body.name,
        description=body.description,
        parent_type_id=body.parent_type_id,
    )


@router.put("/schema/types/{type_id}", response_model=OntologyType)
async def update_ontology_type(
    type_id: str,
    request: Request,
    body: UpdateTypeRequest,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Update an existing ontology type."""
    updated = await repo.update_type(
        type_id=type_id,
        name=body.name,
        description=body.description,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Type {type_id} not found")
    return updated


@router.delete("/schema/types/{type_id}")
async def delete_ontology_type(
    type_id: str,
    request: Request,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Delete (soft-delete) an ontology type."""
    deleted = await repo.delete_type(type_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Type {type_id} not found")
    return delete_ontology_typeResult.model_validate({"deleted": True})


# Property Endpoints

@router.post("/schema/types/{type_id}/properties", response_model=OntologyType)
async def add_type_property(
    type_id: str,
    property: OntologyProperty,
    request: Request,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Add a property to an ontology type."""
    try:
        return await repo.add_property(type_id, property)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/schema/types/{type_id}/properties/{property_id}", response_model=OntologyType)
async def update_type_property(
    type_id: str,
    property_id: str,
    property: OntologyProperty,
    request: Request,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Update a property of an ontology type."""
    try:
        return await repo.update_property(type_id, property_id, property)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/schema/types/{type_id}/properties/{property_id}")
async def remove_type_property(
    type_id: str,
    property_id: str,
    request: Request,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Remove a property from an ontology type."""
    try:
        removed = await repo.remove_property(type_id, property_id)
        if not removed:
            raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
        return remove_type_propertyResult.model_validate({"removed": True})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Relationship Endpoints

@router.get("/schema/relationships", response_model=list[TypeRelationship])
async def list_type_relationships(
    request: Request,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """List all type relationships for the current tenant."""
    return await repo.get_all_relationships()


@router.post("/schema/relationships", response_model=TypeRelationship)
async def create_type_relationship(
    request: Request,
    body: CreateRelationshipRequest,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Create a new relationship between types."""
    relationship = TypeRelationship(
        source_type_id=body.source_type_id,
        target_type_id=body.target_type_id,
        relationship_type=body.relationship_type,
        description=body.description,
        cardinality=body.cardinality,
    )

    return await repo.add_relationship(relationship)


@router.delete("/schema/relationships/{relationship_id}")
async def delete_type_relationship(
    relationship_id: str,
    request: Request,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Delete a type relationship."""
    deleted = await repo.remove_relationship(relationship_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Relationship {relationship_id} not found")
    return delete_type_relationshipResult.model_validate({"deleted": True})


# Version History Endpoints

@router.get("/schema/versions")
async def list_schema_versions(
    request: Request,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """List all published schema versions."""
    versions = await repo.list_schema_versions()
    return [
        {
            "id": v.id,
            "version": v.version,
            "published_by": v.published_by,
            "published_at": v.published_at.isoformat(),
            "comment": v.comment,
        }
        for v in versions
    ]


@router.get("/schema/versions/{version}", response_model=OntologySchema)
async def get_schema_version(
    version: str,
    request: Request,
    repo: OntologySchemaRepository = Depends(get_repository),
):
    """Get a specific published schema version."""
    schema = await repo.get_schema_version(version)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Version {version} not found")
    return schema
