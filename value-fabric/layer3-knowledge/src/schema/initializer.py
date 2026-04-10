"""Schema initializer for Neo4j Knowledge Graph."""

import logging
from typing import List, Optional

from neo4j import AsyncDriver
from ..db.driver import get_driver
from neo4j.exceptions import (
    ClientError,
    ConfigurationError,
    DatabaseError,
    TransientError,
    ServiceUnavailable,
)

from ..config import Settings, get_settings
from .constraints import CONSTRAINTS, INDEXES, Constraint, Index

logger = logging.getLogger(__name__)


class SchemaInitializer:
    """Initialize and manage Neo4j schema for Value Fabric."""

    def __init__(self, driver: Optional[AsyncDriver] = None, settings: Optional[Settings] = None):
        """Initialize schema manager.

        Args:
            driver: Neo4j async driver. If None, creates new connection.
            settings: Application settings. If None, loads from environment.
        """
        self.settings = settings or get_settings()
        self._driver = driver
        self._owned_driver = driver is None

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

    async def initialize_schema(self, drop_existing: bool = False) -> None:
        """Initialize all schema elements.

        Args:
            drop_existing: If True, drops existing constraints/indexes first.
        """
        driver = await self._get_driver()

        async with driver.session(database=self.settings.neo4j_database) as session:
            if drop_existing:
                await self._drop_all_constraints_and_indexes(session)

            # Create constraints first (required for data integrity)
            await self._create_constraints(session)

            # Create indexes (can be done in parallel with constraints)
            await self._create_indexes(session)

            logger.info("Schema initialization complete")

    async def _create_constraints(self, session) -> None:
        """Create all schema constraints."""
        for constraint in CONSTRAINTS:
            try:
                await session.run(constraint.cypher)
                logger.info(f"Created constraint: {constraint.name}")
            except ClientError as e:
                if "already exists" in str(e):
                    logger.info(f"Constraint {constraint.name} already exists")
                else:
                    logger.error(f"Client error creating constraint {constraint.name}: {e}")
                    raise
            except (ConfigurationError, DatabaseError) as e:
                logger.error(f"Database error creating constraint {constraint.name}: {e}")
                raise
            except (TransientError, ServiceUnavailable) as e:
                logger.warning(f"Transient error creating constraint {constraint.name}, retry may be needed: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error creating constraint {constraint.name}: {e}")
                raise

    async def _create_indexes(self, session) -> None:
        """Create all schema indexes."""
        for index in INDEXES:
            try:
                await session.run(index.cypher)
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
                logger.warning(f"Transient error creating index {index.name}, retry may be needed: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error creating index {index.name}: {e}")
                raise

    async def _drop_all_constraints_and_indexes(self, session) -> None:
        """Drop all existing constraints and indexes."""
        # Drop constraints
        for constraint in CONSTRAINTS:
            try:
                await session.run(constraint.drop_cypher)
                logger.info(f"Dropped constraint: {constraint.name}")
            except ClientError as e:
                if "does not exist" in str(e):
                    logger.debug(f"Constraint {constraint.name} does not exist, skipping")
                else:
                    logger.warning(f"Client error dropping constraint {constraint.name}: {e}")
            except (ConfigurationError, DatabaseError) as e:
                logger.warning(f"Database error dropping constraint {constraint.name}: {e}")
            except (TransientError, ServiceUnavailable) as e:
                logger.warning(f"Transient error dropping constraint {constraint.name}, retry may be needed: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error dropping constraint {constraint.name}: {e}")

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
                logger.warning(f"Transient error dropping index {index.name}, retry may be needed: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error dropping index {index.name}: {e}")

    async def verify_schema(self) -> dict:
        """Verify that all schema elements exist.

        Returns:
            Dictionary with verification results.
        """
        driver = await self._get_driver()
        results = {
            "constraints": {"expected": len(CONSTRAINTS), "found": 0, "missing": []},
            "indexes": {"expected": len(INDEXES), "found": 0, "missing": []},
        }

        async with driver.session(database=self.settings.neo4j_database) as session:
            # Check constraints
            constraint_records = await session.run("SHOW CONSTRAINTS YIELD name")
            existing_constraints = [record["name"] async for record in constraint_records]

            for constraint in CONSTRAINTS:
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
        stats = {"nodes": {}, "relationships": {}, "total_nodes": 0, "total_relationships": 0}

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
                return {"status": "unhealthy", "error": "Query returned unexpected result"}
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
