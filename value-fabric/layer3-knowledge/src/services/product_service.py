"""Product Portfolio Service for Knowledge Graph operations.

Manages Product, Feature, and Capability nodes and their relationships
in Neo4j. Provides product-to-capability mapping, signal-to-product
matching, and portfolio analytics.

Architecture:
    - Products are top-level nodes representing sellable offerings
    - Features are child nodes linked via HAS_FEATURE
    - Capabilities are linked via ENABLES_CAPABILITY
    - PainSignals are matched to Products via ADDRESSES_PAIN
    - All queries are tenant-scoped via tenant_id property
"""

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from neo4j import AsyncDriver

try:
    from shared.identity.context import require_context
except ImportError:
    require_context = None

logger = structlog.get_logger()


def _get_tenant_id() -> str:
    """Safely retrieve tenant ID from request context.

    Returns "default" if context is not available (e.g., in tests or background tasks).
    """
    if not require_context:
        return "default"
    try:
        return str(require_context().tenant_id)
    except RuntimeError:
        return "default"


# ---------------------------------------------------------------------------
# Data Transfer Objects
# ---------------------------------------------------------------------------

class ProductCreate:
    """Input for creating a product node."""

    def __init__(
        self,
        name: str,
        description: str,
        category: str | None = None,
        sku: str | None = None,
        pricing_model: str | None = None,
        target_personas: list[str] | None = None,
        industries: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.name = name
        self.description = description
        self.category = category
        self.sku = sku
        self.pricing_model = pricing_model
        self.target_personas = target_personas or []
        self.industries = industries or []
        self.metadata = metadata or {}


class FeatureCreate:
    """Input for creating a feature node linked to a product."""

    def __init__(
        self,
        name: str,
        description: str,
        feature_type: str = "core",
        maturity: str = "ga",
        metadata: dict[str, Any] | None = None,
    ):
        self.name = name
        self.description = description
        self.feature_type = feature_type  # core, addon, premium
        self.maturity = maturity  # beta, ga, deprecated
        self.metadata = metadata or {}


class ProductService:
    """Service for product portfolio graph operations."""

    def __init__(self, driver: AsyncDriver):
        self._driver = driver

    # ------------------------------------------------------------------
    # Product CRUD
    # ------------------------------------------------------------------

    async def create_product(
        self, product: ProductCreate
    ) -> dict[str, Any]:
        """Create a Product node in the knowledge graph."""
        tenant_id = _get_tenant_id()
        product_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        query = """
        CREATE (p:Product {
            id: $id,
            tenant_id: $tenant_id,
            name: $name,
            description: $description,
            category: $category,
            sku: $sku,
            pricing_model: $pricing_model,
            target_personas: $target_personas,
            industries: $industries,
            entity_type: 'Product',
            created_at: datetime($now),
            updated_at: datetime($now)
        })
        RETURN p {.id, .name, .description, .category, .sku,
                   .pricing_model, .target_personas, .industries,
                   .created_at} AS product
        """
        async with self._driver.session() as session:
            result = await session.run(
                query,
                {
                    "id": product_id,
                    "tenant_id": tenant_id,
                    "name": product.name,
                    "description": product.description,
                    "category": product.category,
                    "sku": product.sku,
                    "pricing_model": product.pricing_model,
                    "target_personas": product.target_personas,
                    "industries": product.industries,
                    "now": now,
                },
            )
            record = await result.single()
            logger.info(
                "product_created",
                product_id=product_id,
                tenant_id=tenant_id,
                name=product.name,
            )
            return {"id": product_id, **(record["product"] if record else {})}

    async def get_product(
        self, product_id: str
    ) -> dict[str, Any] | None:
        """Get a single product by ID, scoped to tenant."""
        tenant_id = _get_tenant_id()
        query = """
        MATCH (p:Product {id: $product_id, tenant_id: $tenant_id})
        OPTIONAL MATCH (p)-[:HAS_FEATURE]->(f:Feature)
        OPTIONAL MATCH (p)-[:ENABLES_CAPABILITY]->(c:Capability)
        RETURN p {.id, .name, .description, .category, .sku,
                   .pricing_model, .target_personas, .industries,
                   .created_at, .updated_at} AS product,
               collect(DISTINCT f {.id, .name, .feature_type, .maturity}) AS features,
               collect(DISTINCT c {.id, .name}) AS capabilities
        """
        async with self._driver.session() as session:
            result = await session.run(
                query,
                {"product_id": product_id, "tenant_id": tenant_id},
            )
            record = await result.single()
            if not record or not record["product"]:
                return None
            return {
                **record["product"],
                "features": record["features"],
                "capabilities": record["capabilities"],
            }

    async def list_products(
        self,
        tenant_id: str,
        category: str | None = None,
        industry: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """List products with optional filtering."""
        where_clauses = ["p.tenant_id = $tenant_id"]
        params: dict[str, Any] = {
            "tenant_id": tenant_id,
            "skip": skip,
            "limit": limit,
        }

        if category:
            where_clauses.append("p.category = $category")
            params["category"] = category
        if industry:
            where_clauses.append("$industry IN p.industries")
            params["industry"] = industry

        where = " AND ".join(where_clauses)

        count_query = f"""
        MATCH (p:Product) WHERE {where}
        RETURN count(p) AS total
        """
        list_query = f"""
        MATCH (p:Product) WHERE {where}
        OPTIONAL MATCH (p)-[:HAS_FEATURE]->(f:Feature)
        OPTIONAL MATCH (p)-[:ENABLES_CAPABILITY]->(c:Capability)
        RETURN p {{.id, .name, .description, .category, .sku,
                    .pricing_model, .industries, .created_at}} AS product,
               count(DISTINCT f) AS feature_count,
               count(DISTINCT c) AS capability_count
        ORDER BY p.name
        SKIP $skip LIMIT $limit
        """

        async with self._driver.session() as session:
            count_result = await session.run(count_query, params)
            count_record = await count_result.single()
            total = count_record["total"] if count_record else 0

            list_result = await session.run(list_query, params)
            records = [record async for record in list_result]

            products = []
            for record in records:
                products.append({
                    **record["product"],
                    "feature_count": record["feature_count"],
                    "capability_count": record["capability_count"],
                })

            return {"products": products, "total": total, "skip": skip, "limit": limit}

    async def update_product(
        self, product_id: str, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update a product's properties."""
        tenant_id = _get_tenant_id()
        # Only allow safe property updates
        allowed_fields = {
            "name", "description", "category", "sku",
            "pricing_model", "target_personas", "industries",
        }
        safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        if not safe_updates:
            return await self.get_product(product_id)

        set_clauses = ", ".join(f"p.{k} = ${k}" for k in safe_updates)
        query = f"""
        MATCH (p:Product {{id: $product_id, tenant_id: $tenant_id}})
        SET {set_clauses}, p.updated_at = datetime($now)
        RETURN p {{.id, .name, .description, .category}} AS product
        """
        params = {
            "product_id": product_id,
            "tenant_id": tenant_id,
            "now": datetime.now(UTC).isoformat(),
            **safe_updates,
        }

        async with self._driver.session() as session:
            result = await session.run(query, params)
            record = await result.single()
            if not record:
                return None
            logger.info("product_updated", product_id=product_id, fields=list(safe_updates))
            return record["product"]

    async def delete_product(self, product_id: str) -> bool:
        """Delete a product and its orphaned features."""
        tenant_id = _get_tenant_id()
        query = """
        MATCH (p:Product {id: $product_id, tenant_id: $tenant_id})
        OPTIONAL MATCH (p)-[:HAS_FEATURE]->(f:Feature)
        WHERE NOT exists { (f)<-[:HAS_FEATURE]-(:Product) WHERE NOT (f)<-[:HAS_FEATURE]-(p) }
        DETACH DELETE p, f
        RETURN count(p) AS deleted
        """
        async with self._driver.session() as session:
            result = await session.run(
                query, {"product_id": product_id, "tenant_id": tenant_id}
            )
            record = await result.single()
            deleted = record["deleted"] > 0 if record else False
            if deleted:
                logger.info("product_deleted", product_id=product_id, tenant_id=tenant_id)
            return deleted

    # ------------------------------------------------------------------
    # Feature Management
    # ------------------------------------------------------------------

    async def add_feature(
        self, tenant_id: str, product_id: str, feature: FeatureCreate
    ) -> dict[str, Any] | None:
        """Add a feature to a product."""
        feature_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        query = """
        MATCH (p:Product {id: $product_id, tenant_id: $tenant_id})
        CREATE (f:Feature {
            id: $feature_id,
            tenant_id: $tenant_id,
            name: $name,
            description: $description,
            feature_type: $feature_type,
            maturity: $maturity,
            entity_type: 'Feature',
            created_at: datetime($now),
            updated_at: datetime($now)
        })
        CREATE (p)-[:HAS_FEATURE {created_at: datetime($now)}]->(f)
        RETURN f {.id, .name, .description, .feature_type, .maturity} AS feature
        """
        async with self._driver.session() as session:
            result = await session.run(
                query,
                {
                    "product_id": product_id,
                    "tenant_id": tenant_id,
                    "feature_id": feature_id,
                    "name": feature.name,
                    "description": feature.description,
                    "feature_type": feature.feature_type,
                    "maturity": feature.maturity,
                    "now": now,
                },
            )
            record = await result.single()
            if not record:
                return None  # Product not found
            logger.info(
                "feature_added",
                feature_id=feature_id,
                product_id=product_id,
            )
            return {"id": feature_id, **record["feature"]}

    async def remove_feature(
        self, tenant_id: str, product_id: str, feature_id: str
    ) -> bool:
        """Remove a feature from a product."""
        query = """
        MATCH (p:Product {id: $product_id, tenant_id: $tenant_id})
              -[r:HAS_FEATURE]->(f:Feature {id: $feature_id})
        DELETE r
        WITH f
        WHERE NOT exists { (f)<-[:HAS_FEATURE]-(:Product) }
        DETACH DELETE f
        RETURN true AS removed
        """
        async with self._driver.session() as session:
            result = await session.run(
                query,
                {
                    "product_id": product_id,
                    "tenant_id": tenant_id,
                    "feature_id": feature_id,
                },
            )
            record = await result.single()
            return bool(record)

    # ------------------------------------------------------------------
    # Capability Linking
    # ------------------------------------------------------------------

    async def link_capability(
        self,
        tenant_id: str,
        product_id: str,
        capability_id: str,
        strength: float = 1.0,
    ) -> dict[str, Any] | None:
        """Link a product to an existing capability node."""
        query = """
        MATCH (p:Product {id: $product_id, tenant_id: $tenant_id})
        MATCH (c:Capability {id: $capability_id})
        WHERE c.tenant_id = $tenant_id OR c.tenant_id IS NULL
        MERGE (p)-[r:ENABLES_CAPABILITY]->(c)
        ON CREATE SET r.strength = $strength, r.created_at = datetime()
        ON MATCH SET r.strength = $strength, r.updated_at = datetime()
        RETURN c {.id, .name} AS capability, r.strength AS strength
        """
        async with self._driver.session() as session:
            result = await session.run(
                query,
                {
                    "product_id": product_id,
                    "tenant_id": tenant_id,
                    "capability_id": capability_id,
                    "strength": strength,
                },
            )
            record = await result.single()
            if not record:
                return None
            return {
                "capability": record["capability"],
                "strength": record["strength"],
            }

    async def unlink_capability(
        self, tenant_id: str, product_id: str, capability_id: str
    ) -> bool:
        """Remove the ENABLES_CAPABILITY relationship."""
        query = """
        MATCH (p:Product {id: $product_id, tenant_id: $tenant_id})
              -[r:ENABLES_CAPABILITY]->(c:Capability {id: $capability_id})
        DELETE r
        RETURN true AS removed
        """
        async with self._driver.session() as session:
            result = await session.run(
                query,
                {
                    "product_id": product_id,
                    "tenant_id": tenant_id,
                    "capability_id": capability_id,
                },
            )
            record = await result.single()
            return bool(record)

    # ------------------------------------------------------------------
    # Signal-to-Product Matching
    # ------------------------------------------------------------------

    async def match_signals_to_products(
        self, tenant_id: str, account_id: str | None = None, min_confidence: float = 0.5
    ) -> list[dict[str, Any]]:
        """Match PainSignals to Products via shared Capabilities.

        The matching logic:
        1. PainSignal -[:INDICATES_NEED_FOR]-> Capability
        2. Product -[:ENABLES_CAPABILITY]-> Capability
        3. Score = sum(signal.confidence * relationship.strength)
        """
        where_clauses = ["ps.tenant_id = $tenant_id", "ps.confidence_score >= $min_confidence"]
        params: dict[str, Any] = {
            "tenant_id": tenant_id,
            "min_confidence": min_confidence,
        }

        if account_id:
            where_clauses.append("ps.account_id = $account_id")
            params["account_id"] = account_id

        where = " AND ".join(where_clauses)

        query = f"""
        MATCH (ps:PainSignal)-[:INDICATES_NEED_FOR]->(c:Capability)<-[ec:ENABLES_CAPABILITY]-(p:Product)
        WHERE {where} AND p.tenant_id = $tenant_id
        WITH p, ps, c,
             ps.confidence_score * COALESCE(ec.strength, 1.0) AS match_score
        ORDER BY match_score DESC
        WITH p,
             collect(DISTINCT {{
                 signal_id: ps.id,
                 signal_name: ps.name,
                 capability_id: c.id,
                 capability_name: c.name,
                 score: match_score
             }}) AS matches,
             sum(match_score) AS total_score,
             count(DISTINCT ps) AS signal_count
        RETURN p {{.id, .name, .category}} AS product,
               total_score,
               signal_count,
               matches[0..5] AS top_matches
        ORDER BY total_score DESC
        """

        async with self._driver.session() as session:
            result = await session.run(query, params)
            records = [record async for record in result]
            return [
                {
                    "product": record["product"],
                    "total_score": record["total_score"],
                    "signal_count": record["signal_count"],
                    "top_matches": record["top_matches"],
                }
                for record in records
            ]

    # ------------------------------------------------------------------
    # Portfolio Analytics
    # ------------------------------------------------------------------

    async def get_portfolio_summary(self) -> dict[str, Any]:
        """Get a summary of the product portfolio for a tenant."""
        tenant_id = _get_tenant_id()
        query = """
        MATCH (p:Product {tenant_id: $tenant_id})
        OPTIONAL MATCH (p)-[:HAS_FEATURE]->(f:Feature)
        OPTIONAL MATCH (p)-[:ENABLES_CAPABILITY]->(c:Capability)
        WITH p, count(DISTINCT f) AS features, count(DISTINCT c) AS capabilities
        RETURN count(p) AS total_products,
               sum(features) AS total_features,
               sum(capabilities) AS total_capabilities,
               collect(DISTINCT p.category) AS categories,
               avg(features) AS avg_features_per_product,
               avg(capabilities) AS avg_capabilities_per_product
        """
        async with self._driver.session() as session:
            result = await session.run(query, {"tenant_id": tenant_id})
            record = await result.single()
            if not record:
                return {
                    "total_products": 0,
                    "total_features": 0,
                    "total_capabilities": 0,
                    "categories": [],
                }
            return {
                "total_products": record["total_products"],
                "total_features": record["total_features"],
                "total_capabilities": record["total_capabilities"],
                "categories": [c for c in record["categories"] if c],
                "avg_features_per_product": round(record["avg_features_per_product"] or 0, 1),
                "avg_capabilities_per_product": round(record["avg_capabilities_per_product"] or 0, 1),
            }

    async def get_capability_coverage(self) -> list[dict[str, Any]]:
        """Show which capabilities are covered by products and which are gaps."""
        tenant_id = _get_tenant_id()
        query = """
        MATCH (c:Capability)
        WHERE c.tenant_id = $tenant_id OR c.tenant_id IS NULL
        OPTIONAL MATCH (p:Product {tenant_id: $tenant_id})-[ec:ENABLES_CAPABILITY]->(c)
        OPTIONAL MATCH (ps:PainSignal {tenant_id: $tenant_id})-[:INDICATES_NEED_FOR]->(c)
        RETURN c {.id, .name} AS capability,
               collect(DISTINCT p {.id, .name}) AS products,
               count(DISTINCT ps) AS signal_demand,
               CASE WHEN count(p) > 0 THEN 'covered' ELSE 'gap' END AS status
        ORDER BY signal_demand DESC
        """
        async with self._driver.session() as session:
            result = await session.run(query, {"tenant_id": tenant_id})
            records = [record async for record in result]
            return [
                {
                    "capability": record["capability"],
                    "products": record["products"],
                    "signal_demand": record["signal_demand"],
                    "status": record["status"],
                }
                for record in records
            ]
