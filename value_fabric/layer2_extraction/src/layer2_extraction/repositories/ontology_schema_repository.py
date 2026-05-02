"""Repository for ontology schema database operations."""

from datetime import UTC, datetime
from uuid import uuid4

import asyncpg

# Constants for default values
DEFAULT_SCHEMA_VERSION = "1.0.0"
DEFAULT_TENANT_ID = "default"
SYSTEM_USER_ID = "system"

from shared.identity.context import require_context

from layer2_extraction.db import get_connection
from layer2_extraction.models.ontology import (
    OntologyProperty,
    OntologySchema,
    OntologyType,
    PropertyConstraints,
    SchemaVersion,
    TypeRelationship,
)


class OntologySchemaRepository:
    """Repository for ontology schema CRUD operations.

    Provides methods for managing ontology type definitions, properties,
    and relationships in the database with tenant isolation.
    """

    # ==========================================================================
    # Schema Operations
    # ==========================================================================

    async def get_schema(self) -> OntologySchema:
        """Get the complete ontology schema for a tenant.

        Returns:
            OntologySchema containing all types and relationships
        """
        types = await self.get_all_types()
        relationships = await self.get_all_relationships()

        # Get latest published version info
        version = await self._get_latest_version()

        return OntologySchema(
            types=types,
            relationships=relationships,
            version=version.version if version else DEFAULT_SCHEMA_VERSION,
            published_at=version.published_at if version else None,
            published_by=version.published_by if version else None,
        )

    async def _get_latest_version(self) -> SchemaVersion | None:
        """Get the latest published schema version for a tenant."""
        tenant_id = str(require_context().tenant_id)
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, tenant_id, version, schema_json, published_by, published_at, comment
                FROM ontology_schema_versions
                WHERE tenant_id = $1
                ORDER BY published_at DESC
                LIMIT 1
                """,
                tenant_id,
            )
            if row:
                return SchemaVersion(**dict(row))
            return None

    # ==========================================================================
    # Type Operations
    # ==========================================================================

    async def get_all_types(self) -> list[OntologyType]:
        """Get all ontology types for a tenant.

        Uses a single JOIN query to avoid N+1 query pattern when fetching properties.
        """
        tenant_id = str(require_context().tenant_id)
        async with get_connection() as conn:
            # Fetch all types
            type_rows = await conn.fetch(
                """
                SELECT id, tenant_id, name, description, parent_type_id,
                       created_at, updated_at, version, is_active
                FROM ontology_types
                WHERE tenant_id = $1 AND is_active = TRUE
                ORDER BY name
                """,
                tenant_id,
            )

            if not type_rows:
                return []

            # Fetch all properties for these types in a single query
            type_ids = [row["id"] for row in type_rows]
            prop_rows = await conn.fetch(
                """
                SELECT id, type_id, name, property_type, description, required,
                       default_value, constraints, display_order
                FROM ontology_properties
                WHERE type_id = ANY($1)
                ORDER BY type_id, display_order, name
                """,
                type_ids,
            )

            # Group properties by type_id
            props_by_type: dict[str, list[OntologyProperty]] = {}
            for row in prop_rows:
                type_id = row["type_id"]
                if type_id not in props_by_type:
                    props_by_type[type_id] = []

                constraints = None
                if row["constraints"]:
                    constraints = PropertyConstraints(**row["constraints"])

                props_by_type[type_id].append(OntologyProperty(
                    id=row["id"],
                    name=row["name"],
                    type=row["property_type"],
                    description=row["description"] or "",
                    required=row["required"],
                    default_value=row["default_value"],
                    constraints=constraints,
                ))

            # Build OntologyType objects with pre-fetched properties
            types = []
            for row in type_rows:
                types.append(OntologyType(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    properties=props_by_type.get(row["id"], []),
                    parent_type_id=row["parent_type_id"],
                    is_active=row["is_active"],
                    version=row["version"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                ))
            return types

    async def _get_properties_for_type(
        self, conn: asyncpg.Connection, type_id: str
    ) -> list[OntologyProperty]:
        """Get all properties for a type."""
        rows = await conn.fetch(
            """
            SELECT id, name, property_type, description, required,
                   default_value, constraints, display_order
            FROM ontology_properties
            WHERE type_id = $1
            ORDER BY display_order, name
            """,
            type_id,
        )

        properties = []
        for row in rows:
            constraints = None
            if row["constraints"]:
                constraints = PropertyConstraints(**row["constraints"])

            properties.append(OntologyProperty(
                id=row["id"],
                name=row["name"],
                type=row["property_type"],
                description=row["description"],
                required=row["required"],
                default_value=row["default_value"],
                constraints=constraints,
            ))
        return properties

    async def get_type_by_id(self, type_id: str) -> OntologyType | None:
        """Get a specific type by ID."""
        tenant_id = str(require_context().tenant_id)
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, tenant_id, name, description, parent_type_id,
                       created_at, updated_at, version, is_active
                FROM ontology_types
                WHERE tenant_id = $1 AND id = $2 AND is_active = TRUE
                """,
                tenant_id,
                type_id,
            )
            if not row:
                return None

            properties = await self._get_properties_for_type(conn, row["id"])
            return OntologyType(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                properties=properties,
                parent_type_id=row["parent_type_id"],
                is_active=row["is_active"],
                version=row["version"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def create_type(
        self, name: str, description: str,
        parent_type_id: str | None = None
    ) -> OntologyType:
        """Create a new ontology type."""
        tenant_id = str(require_context().tenant_id)
        type_id = str(uuid4())
        now = datetime.now(UTC)

        async with get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO ontology_types (id, tenant_id, name, description, parent_type_id,
                                           created_at, updated_at, version, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, 1, TRUE)
                """,
                type_id, tenant_id, name, description, parent_type_id, now, now,
            )

        return OntologyType(
            id=type_id,
            name=name,
            description=description,
            properties=[],
            parent_type_id=parent_type_id,
            is_active=True,
            version=1,
            created_at=now,
            updated_at=now,
        )

    async def update_type(
        self, type_id: str,
        name: str | None = None, description: str | None = None
    ) -> OntologyType | None:
        """Update an ontology type."""
        tenant_id = str(require_context().tenant_id)
        now = datetime.now(UTC)

        async with get_connection() as conn:
            # Build dynamic update
            updates = []
            params = [now]  # updated_at is always set

            if name is not None:
                updates.append(f"name = ${len(params) + 1}")
                params.append(name)
            if description is not None:
                updates.append(f"description = ${len(params) + 1}")
                params.append(description)

            if not updates:
                return await self.get_type_by_id(tenant_id, type_id)

            updates.append("updated_at = $1")
            updates.append("version = version + 1")

            query = f"""
                UPDATE ontology_types
                SET {', '.join(updates)}
                WHERE tenant_id = $2 AND id = $3
                RETURNING id, tenant_id, name, description, parent_type_id,
                         created_at, updated_at, version, is_active
            """
            params = [now, tenant_id, type_id] + params[1:]  # Reorder params

            row = await conn.fetchrow(query, *params)
            if not row:
                return None

            properties = await self._get_properties_for_type(conn, type_id)
            return OntologyType(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                properties=properties,
                parent_type_id=row["parent_type_id"],
                is_active=row["is_active"],
                version=row["version"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def delete_type(self, type_id: str) -> bool:
        """Soft delete an ontology type."""
        tenant_id = str(require_context().tenant_id)
        async with get_connection() as conn:
            result = await conn.execute(
                """
                UPDATE ontology_types
                SET is_active = FALSE, updated_at = NOW()
                WHERE tenant_id = $1 AND id = $2
                """,
                tenant_id,
                type_id,
            )
            # Check if any row was updated
            return "UPDATE 1" in result

    # ==========================================================================
    # Property Operations
    # ==========================================================================

    async def add_property(
        self, type_id: str, property: OntologyProperty
    ) -> OntologyType:
        """Add a property to a type."""
        tenant_id = str(require_context().tenant_id)
        async with get_connection() as conn:
            # Verify type exists and belongs to tenant
            type_row = await conn.fetchrow(
                "SELECT id FROM ontology_types WHERE tenant_id = $1 AND id = $2",
                tenant_id, type_id,
            )
            if not type_row:
                raise ValueError(f"Type {type_id} not found")

            # Get next display order
            max_order = await conn.fetchval(
                "SELECT MAX(display_order) FROM ontology_properties WHERE type_id = $1",
                type_id,
            ) or 0

            constraints_json = None
            if property.constraints:
                constraints_json = property.constraints.model_dump(exclude_none=True)

            await conn.execute(
                """
                INSERT INTO ontology_properties
                (id, type_id, name, property_type, description, required,
                 default_value, constraints, display_order)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (type_id, name) DO UPDATE SET
                property_type = EXCLUDED.property_type,
                description = EXCLUDED.description,
                required = EXCLUDED.required,
                default_value = EXCLUDED.default_value,
                constraints = EXCLUDED.constraints
                """,
                property.id,
                type_id,
                property.name,
                property.type.value if hasattr(property.type, 'value') else str(property.type),
                property.description,
                property.required,
                property.default_value,
                constraints_json,
                max_order + 1,
            )

            # Update type timestamp and version
            await conn.execute(
                """
                UPDATE ontology_types
                SET updated_at = NOW(), version = version + 1
                WHERE id = $1
                """,
                type_id,
            )

        return await self.get_type_by_id(type_id)

    async def update_property(
        self, type_id: str, property_id: str,
        property: OntologyProperty
    ) -> OntologyType:
        """Update a property."""
        tenant_id = str(require_context().tenant_id)
        async with get_connection() as conn:
            # Verify type ownership
            type_row = await conn.fetchrow(
                "SELECT id FROM ontology_types WHERE tenant_id = $1 AND id = $2",
                tenant_id, type_id,
            )
            if not type_row:
                raise ValueError(f"Type {type_id} not found")

            constraints_json = None
            if property.constraints:
                constraints_json = property.constraints.model_dump(exclude_none=True)

            await conn.execute(
                """
                UPDATE ontology_properties
                SET name = $1, property_type = $2, description = $3,
                    required = $4, default_value = $5, constraints = $6
                WHERE id = $7 AND type_id = $8
                """,
                property.name,
                property.type.value if hasattr(property.type, 'value') else str(property.type),
                property.description,
                property.required,
                property.default_value,
                constraints_json,
                property_id,
                type_id,
            )

            # Update type timestamp
            await conn.execute(
                "UPDATE ontology_types SET updated_at = NOW(), version = version + 1 WHERE id = $1",
                type_id,
            )

        return await self.get_type_by_id(type_id)

    async def remove_property(self, type_id: str, property_id: str) -> bool:
        """Remove a property from a type."""
        tenant_id = str(require_context().tenant_id)
        async with get_connection() as conn:
            # Verify type ownership
            type_row = await conn.fetchrow(
                "SELECT id FROM ontology_types WHERE tenant_id = $1 AND id = $2",
                tenant_id, type_id,
            )
            if not type_row:
                raise ValueError(f"Type {type_id} not found")

            result = await conn.execute(
                "DELETE FROM ontology_properties WHERE id = $1 AND type_id = $2",
                property_id, type_id,
            )

            if "DELETE 1" in result:
                # Update type timestamp
                await conn.execute(
                    "UPDATE ontology_types SET updated_at = NOW(), version = version + 1 WHERE id = $1",
                    type_id,
                )
                return True
            return False

    # ==========================================================================
    # Relationship Operations
    # ==========================================================================

    async def get_all_relationships(self) -> list[TypeRelationship]:
        """Get all type relationships for a tenant."""
        tenant_id = str(require_context().tenant_id)
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, tenant_id, source_type_id, target_type_id,
                       relationship_type, description, cardinality, created_at
                FROM ontology_relationships
                WHERE tenant_id = $1
                ORDER BY created_at
                """,
                tenant_id,
            )

            return [
                TypeRelationship(
                    id=row["id"],
                    source_type_id=row["source_type_id"],
                    target_type_id=row["target_type_id"],
                    relationship_type=row["relationship_type"],
                    description=row["description"],
                    cardinality=row["cardinality"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    async def add_relationship(
        self, relationship: TypeRelationship
    ) -> TypeRelationship:
        """Add a relationship between types."""
        tenant_id = str(require_context().tenant_id)
        async with get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO ontology_relationships
                (id, tenant_id, source_type_id, target_type_id,
                 relationship_type, description, cardinality)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (tenant_id, source_type_id, target_type_id, relationship_type)
                DO UPDATE SET description = EXCLUDED.description,
                              cardinality = EXCLUDED.cardinality
                """,
                relationship.id,
                tenant_id,
                relationship.source_type_id,
                relationship.target_type_id,
                relationship.relationship_type.value if hasattr(relationship.relationship_type, 'value') else str(relationship.relationship_type),
                relationship.description,
                relationship.cardinality.value if hasattr(relationship.cardinality, 'value') else str(relationship.cardinality),
            )

        return relationship

    async def remove_relationship(self, relationship_id: str) -> bool:
        """Remove a relationship."""
        tenant_id = str(require_context().tenant_id)
        async with get_connection() as conn:
            result = await conn.execute(
                """
                DELETE FROM ontology_relationships
                WHERE id = $1 AND tenant_id = $2
                """,
                relationship_id,
                tenant_id,
            )
            return "DELETE 1" in result

    # ==========================================================================
    # Version/Publish Operations
    # ==========================================================================

    async def publish_schema(
        self, version: str, user_id: str, comment: str | None = None
    ) -> SchemaVersion:
        """Publish the current schema as a new version."""
        tenant_id = str(require_context().tenant_id)
        # Get current schema
        schema = await self.get_schema()

        # Create version record
        version_id = str(uuid4())
        now = datetime.now(UTC)

        schema_json = schema.model_dump(mode="json")

        async with get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO ontology_schema_versions
                (id, tenant_id, version, schema_json, published_by, published_at, comment)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                version_id,
                tenant_id,
                version,
                schema_json,
                user_id,
                now,
                comment,
            )

        return SchemaVersion(
            id=version_id,
            tenant_id=tenant_id,
            version=version,
            schema_data=schema_json,
            published_by=user_id,
            published_at=now,
            comment=comment,
        )

    async def get_schema_version(
        self, version: str
    ) -> OntologySchema | None:
        """Get a specific published schema version."""
        tenant_id = str(require_context().tenant_id)
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT schema_json
                FROM ontology_schema_versions
                WHERE tenant_id = $1 AND version = $2
                """,
                tenant_id,
                version,
            )
            if row:
                return OntologySchema(**row["schema_json"])
            return None

    async def list_schema_versions(self) -> list[SchemaVersion]:
        """List all published schema versions."""
        tenant_id = str(require_context().tenant_id)
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, tenant_id, version, schema_json, published_by, published_at, comment
                FROM ontology_schema_versions
                WHERE tenant_id = $1
                ORDER BY published_at DESC
                """,
                tenant_id,
            )

            return [SchemaVersion(**dict(row)) for row in rows]

    # ==========================================================================
    # Import/Export Operations
    # ==========================================================================

    async def import_schema(
        self, schema: OntologySchema, user_id: str
    ) -> OntologySchema:
        """Import a complete schema, replacing the current one.

        This operation is atomic - either all changes succeed or none do.
        Type IDs are remapped to new UUIDs to avoid collisions.

        Args:
            schema: The complete ontology schema to import
            user_id: The user performing the import (for audit purposes)

        Returns:
            The imported schema as now stored in the database

        Note:
            This deletes all existing types, properties, and relationships
            for the tenant before importing the new schema.
        """
        tenant_id = str(require_context().tenant_id)
        async with get_connection() as conn:
            async with conn.transaction():
                # Delete existing schema
                await conn.execute(
                    "DELETE FROM ontology_relationships WHERE tenant_id = $1",
                    tenant_id,
                )
                await conn.execute(
                    "DELETE FROM ontology_properties WHERE type_id IN (SELECT id FROM ontology_types WHERE tenant_id = $1)",
                    tenant_id,
                )
                await conn.execute(
                    "DELETE FROM ontology_types WHERE tenant_id = $1",
                    tenant_id,
                )

                # Import types
                type_id_map: dict[str, str] = {}  # old_id -> new_id
                for t in schema.types:
                    new_id = str(uuid4())
                    type_id_map[t.id] = new_id

                    await conn.execute(
                        """
                        INSERT INTO ontology_types
                        (id, tenant_id, name, description, parent_type_id, version, is_active)
                        VALUES ($1, $2, $3, $4, $5, $6, TRUE)
                        """,
                        new_id,
                        tenant_id,
                        t.name,
                        t.description,
                        type_id_map.get(t.parent_type_id, t.parent_type_id),
                        t.version,
                    )

                    # Import properties
                    for p in t.properties:
                        constraints_json = None
                        if p.constraints:
                            constraints_json = p.constraints.model_dump(exclude_none=True)

                        await conn.execute(
                            """
                            INSERT INTO ontology_properties
                            (id, type_id, name, property_type, description, required,
                             default_value, constraints, display_order)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                            """,
                            str(uuid4()),
                            new_id,
                            p.name,
                            p.type.value if hasattr(p.type, 'value') else str(p.type),
                            p.description,
                            p.required,
                            p.default_value,
                            constraints_json,
                            0,
                        )

                # Import relationships
                for r in schema.relationships:
                    await conn.execute(
                        """
                        INSERT INTO ontology_relationships
                        (id, tenant_id, source_type_id, target_type_id,
                         relationship_type, description, cardinality)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        str(uuid4()),
                        tenant_id,
                        type_id_map.get(r.source_type_id, r.source_type_id),
                        type_id_map.get(r.target_type_id, r.target_type_id),
                        r.relationship_type.value if hasattr(r.relationship_type, 'value') else str(r.relationship_type),
                        r.description,
                        r.cardinality.value if hasattr(r.cardinality, 'value') else str(r.cardinality),
                    )

        # Return the imported schema
        return await self.get_schema()
