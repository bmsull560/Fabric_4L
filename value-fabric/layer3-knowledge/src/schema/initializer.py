"""Schema initializer for Neo4j Knowledge Graph."""

import logging

from neo4j import AsyncDriver
from neo4j.exceptions import (
    ClientError,
    ConfigurationError,
    DatabaseError,
    ServiceUnavailable,
    TransientError,
)

from ..config import Settings, get_settings
from ..db.driver import get_driver
from .constraints import CONSTRAINTS, INDEXES, TENANT_CONSTRAINTS

logger = logging.getLogger(__name__)


class SchemaInitializer:
    """Initialize and manage Neo4j schema for Value Fabric."""

    def __init__(
        self, driver: AsyncDriver | None = None, settings: Settings | None = None
    ):
        """Initialize schema manager.

        Args:
            driver: Neo4j async driver. If None, creates new connection.
            settings: Application settings. If None, loads from environment.
        """
        self.settings = settings or get_settings()
        self._driver = driver
        self._owned_driver = driver is None
        self._edition: str | None = None

    async def _get_driver(self) -> AsyncDriver:
        """Get or create Neo4j driver via the shared singleton factory."""
        if self._driver is None:
            self._driver = await get_driver(self.settings)
        return self._driver

    async def close(self) -> None:
        """Close Neo4j driver if owned."""
        if self._owned_driver and self._driver:
            await self._driver.close()
            self._driver = None

    async def _detect_edition(self, session) -> str:
        """Detect Neo4j edition (community or enterprise).

        Args:
            session: Neo4j session

        Returns:
            Edition string: "community", "enterprise", or "unknown"
        """
        try:
            result = await session.run("CALL dbms.components() YIELD edition RETURN edition")
            record = await result.single()
            edition = record["edition"].lower() if record else "unknown"
            return edition
        except Exception as e:
            logger.warning(f"Failed to detect Neo4j edition, assuming community: {e}")
            return "community"

    def _is_enterprise(self, edition: str | None = None) -> bool:
        """Check if running on Neo4j Enterprise Edition.

        Args:
            edition: Edition string. If None, uses cached edition from detection.

        Returns:
            True if Enterprise Edition, False otherwise
        """
        ed = edition or self._edition or "community"
        return ed == "enterprise"

    def _get_constraints_for_edition(self, edition: str | None = None) -> list:
        """Get constraints appropriate for the Neo4j edition.

        Args:
            edition: Edition string. If None, uses cached edition.

        Returns:
            List of constraints to create for this edition
        """
        ed = edition or self._edition or "community"
        if ed == "enterprise":
            # Enterprise gets all constraints including property existence
            return CONSTRAINTS + TENANT_CONSTRAINTS
        else:
            # Community only gets basic unique constraints
            return CONSTRAINTS

    async def initialize_schema(self, drop_existing: bool = False) -> None:
        """Initialize all schema elements.

        Args:
            drop_existing: If True, drops existing constraints/indexes first.
        """
        driver = await self._get_driver()

        async with driver.session(database=self.settings.neo4j_database) as session:
            # Detect edition first
            self._edition = await self._detect_edition(session)
            is_enterprise = self._is_enterprise(self._edition)

            if is_enterprise:
                logger.info("Neo4j Enterprise Edition detected - will create all constraints")
            else:
                logger.info(f"Neo4j {self._edition.capitalize()} Edition detected - skipping Enterprise-only constraints")

            if drop_existing:
                await self._drop_all_constraints_and_indexes(session)

            # Create constraints first (required for data integrity)
            await self._create_constraints(session)

            # Create indexes (can be done in parallel with constraints)
            await self._create_indexes(session)

            logger.info("Schema initialization complete")

    async def _create_constraints(self, session) -> None:
        """Create all schema constraints appropriate for the Neo4j edition."""
        constraints = self._get_constraints_for_edition(self._edition)
        skipped = []

        for constraint in constraints:
            try:
                await session.run(constraint.cypher)
                logger.info(f"Created constraint: {constraint.name}")
            except ClientError as e:
                if "already exists" in str(e):
                    logger.info(f"Constraint {constraint.name} already exists")
                else:
                    logger.error(
                        f"Client error creating constraint {constraint.name}: {e}"
                    )
                    raise
            except (ConfigurationError, DatabaseError) as e:
                logger.error(
                    f"Database error creating constraint {constraint.name}: {e}"
                )
                raise
            except (TransientError, ServiceUnavailable) as e:
                logger.warning(
                    f"Transient error creating constraint {constraint.name}, retry may be needed: {e}"
                )
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error creating constraint {constraint.name}: {e}"
                )
                raise

        # Log skipped enterprise constraints
        if not self._is_enterprise() and TENANT_CONSTRAINTS:
            skipped_names = [c.name for c in TENANT_CONSTRAINTS]
            logger.info(f"Skipped Enterprise-only constraints: {skipped_names}")

    async def _create_indexes(self, session) -> None:
        """Create all schema indexes."""
        for index in INDEXES:
            try:
                query = index.cypher
                if index.index_type == "vector":
                    query = self._build_vector_index_cypher(
                        index_name=index.name,
                        entity_type=index.entity_type,
                        property_name=index.properties[0],
                    )
                await session.run(query)
                logger.info(f"Created index: {index.name}")
            except ClientError as e:
                if "already exists" in str(e):
                    logger.info(f"Index {index.name} already exists")
                else:
                    logger.error(f"Client error creating index {index.name}: {e}")
                    raise
            except (ConfigurationError, DatabaseError) as e:
                logger.error(f"Database error creating index {index.name}: {e}")
                raise
            except (TransientError, ServiceUnavailable) as e:
                logger.warning(
                    f"Transient error creating index {index.name}, retry may be needed: {e}"
                )
                raise
            except Exception as e:
                logger.error(f"Unexpected error creating index {index.name}: {e}")
                raise

    def _build_vector_index_cypher(
        self,
        index_name: str,
        entity_type: str,
        property_name: str,
    ) -> str:
        """Build vector index Cypher using configured embedding dimension."""
        embedding_dimension = getattr(self.settings, "embedding_dimension", 384)
        return (
            f"CREATE VECTOR INDEX {index_name} "
            "IF NOT EXISTS "
            f"FOR (n:{entity_type}) "
            f"ON (n.{property_name}) "
            "OPTIONS {indexConfig: {"
            f"`vector.dimensions`: {embedding_dimension}, "
            "`vector.similarity_function`: 'cosine'"
            "}}"
        )

    async def _drop_all_constraints_and_indexes(self, session) -> None:
        """Drop all existing constraints and indexes."""
        # Detect edition if not already cached
        if self._edition is None:
            self._edition = await self._detect_edition(session)

        # Get all constraints for this edition (including enterprise if applicable)
        constraints_to_drop = self._get_constraints_for_edition(self._edition)

        # Drop constraints
        for constraint in constraints_to_drop:
            try:
                await session.run(constraint.drop_cypher)
                logger.info(f"Dropped constraint: {constraint.name}")
            except ClientError as e:
                if "does not exist" in str(e):
                    logger.debug(
                        f"Constraint {constraint.name} does not exist, skipping"
                    )
                else:
                    logger.warning(
                        f"Client error dropping constraint {constraint.name}: {e}"
                    )
            except (ConfigurationError, DatabaseError) as e:
                logger.warning(
                    f"Database error dropping constraint {constraint.name}: {e}"
                )
            except (TransientError, ServiceUnavailable) as e:
                logger.warning(
                    f"Transient error dropping constraint {constraint.name}, retry may be needed: {e}"
                )
            except Exception as e:
                logger.warning(
                    f"Unexpected error dropping constraint {constraint.name}: {e}"
                )

        # Drop indexes
        for index in INDEXES:
            try:
                await session.run(index.drop_cypher)
                logger.info(f"Dropped index: {index.name}")
            except ClientError as e:
                if "does not exist" in str(e):
                    logger.debug(f"Index {index.name} does not exist, skipping")
                else:
                    logger.warning(f"Client error dropping index {index.name}: {e}")
            except (ConfigurationError, DatabaseError) as e:
                logger.warning(f"Database error dropping index {index.name}: {e}")
            except (TransientError, ServiceUnavailable) as e:
                logger.warning(
                    f"Transient error dropping index {index.name}, retry may be needed: {e}"
                )
            except Exception as e:
                logger.warning(f"Unexpected error dropping index {index.name}: {e}")

    async def verify_schema(self) -> dict:
        """Verify that all schema elements exist.

        Returns:
            Dictionary with verification results.
        """
        driver = await self._get_driver()

        async with driver.session(database=self.settings.neo4j_database) as session:
            # Detect edition if not already cached
            if self._edition is None:
                self._edition = await self._detect_edition(session)

            expected_constraints = self._get_constraints_for_edition(self._edition)

            results = {
                "constraints": {"expected": len(expected_constraints), "found": 0, "missing": []},
                "indexes": {"expected": len(INDEXES), "found": 0, "missing": []},
                "edition": self._edition,
                "enterprise_features": self._is_enterprise(),
            }

            # Check constraints
            constraint_records = await session.run("SHOW CONSTRAINTS YIELD name")
            existing_constraints = [
                record["name"] async for record in constraint_records
            ]

            for constraint in expected_constraints:
                if constraint.name in existing_constraints:
                    results["constraints"]["found"] += 1
                else:
                    results["constraints"]["missing"].append(constraint.name)

            # Check indexes
            index_records = await session.run("SHOW INDEXES YIELD name")
            existing_indexes = [record["name"] async for record in index_records]

            for index in INDEXES:
                if index.name in existing_indexes:
                    results["indexes"]["found"] += 1
                else:
                    results["indexes"]["missing"].append(index.name)

        results["valid"] = (
            results["constraints"]["found"] == results["constraints"]["expected"]
            and results["indexes"]["found"] == results["indexes"]["expected"]
        )

        return results

    async def get_statistics(self) -> dict:
        """Get database statistics.

        Returns:
            Dictionary with node and relationship counts by type.
        """
        driver = await self._get_driver()
        stats = {
            "nodes": {},
            "relationships": {},
            "total_nodes": 0,
            "total_relationships": 0,
        }

        async with driver.session(database=self.settings.neo4j_database) as session:
            # Count nodes by label
            node_result = await session.run(
                "MATCH (n) RETURN labels(n) as labels, count(*) as count"
            )
            async for record in node_result:
                labels = record["labels"]
                count = record["count"]
                label_str = ":".join(labels) if labels else "NoLabel"
                stats["nodes"][label_str] = count
                stats["total_nodes"] += count

            # Count relationships by type
            rel_result = await session.run(
                "MATCH ()-[r]->() RETURN type(r) as type, count(*) as count"
            )
            async for record in rel_result:
                rel_type = record["type"]
                count = record["count"]
                stats["relationships"][rel_type] = count
                stats["total_relationships"] += count

        return stats

    async def health_check(self) -> dict:
        """Check Neo4j connectivity and basic functionality.

        Returns:
            Health status dictionary.
        """
        try:
            driver = await self._get_driver()
            async with driver.session(database=self.settings.neo4j_database) as session:
                result = await session.run("RETURN 1 as check")
                record = await result.single()
                if record and record["check"] == 1:
                    return {
                        "status": "healthy",
                        "database": self.settings.neo4j_database,
                        "uri": self.settings.neo4j_uri,
                    }
                return {
                    "status": "unhealthy",
                    "error": "Query returned unexpected result",
                }
        except (ServiceUnavailable, TransientError) as e:
            return {"status": "unhealthy", "error": f"Neo4j service unavailable: {e}"}
        except ConfigurationError as e:
            return {"status": "unhealthy", "error": f"Neo4j configuration error: {e}"}
        except DatabaseError as e:
            return {"status": "unhealthy", "error": f"Neo4j database error: {e}"}
        except ClientError as e:
            return {"status": "unhealthy", "error": f"Neo4j client error: {e}"}
        except Exception as e:
            return {"status": "unhealthy", "error": f"Unexpected error: {e}"}
