"""Neo4j schema definitions for Value Fabric Knowledge Graph.

NOTE: Property existence constraints (constraint_type="exists") require Neo4j
Enterprise Edition. For Community Edition compatibility, use application-level
validation via ingestion.validators.RequiredFieldValidator instead.

The CONSTRAINTS list below uses only unique constraints (constraint_type="unique")
which are supported on both Community and Enterprise editions.
"""

from dataclasses import dataclass


@dataclass
class Constraint:
    """Neo4j constraint definition."""

    name: str
    entity_type: str
    property_name: str
    constraint_type: str = "unique"  # unique (Community+Enterprise), exists (Enterprise only), node_key (Enterprise only)

    @property
    def cypher(self) -> str:
        """Generate Cypher constraint creation statement."""
        if self.constraint_type == "unique":
            return (
                f"CREATE CONSTRAINT {self.name} "
                f"IF NOT EXISTS "
                f"FOR (n:{self.entity_type}) "
                f"REQUIRE n.{self.property_name} IS UNIQUE"
            )
        elif self.constraint_type == "exists":
            return (
                f"CREATE CONSTRAINT {self.name} "
                f"IF NOT EXISTS "
                f"FOR (n:{self.entity_type}) "
                f"REQUIRE n.{self.property_name} IS NOT NULL"
            )
        elif self.constraint_type == "node_key":
            return (
                f"CREATE CONSTRAINT {self.name} "
                f"IF NOT EXISTS "
                f"FOR (n:{self.entity_type}) "
                f"REQUIRE n.{self.property_name} IS NODE KEY"
            )
        return ""

    @property
    def drop_cypher(self) -> str:
        """Generate Cypher constraint drop statement."""
        return f"DROP CONSTRAINT {self.name} IF EXISTS"


@dataclass
class Index:
    """Neo4j index definition."""

    name: str
    entity_type: str
    properties: list[str]
    index_type: str = "btree"  # btree, fulltext, vector, lookup

    @property
    def cypher(self) -> str:
        """Generate Cypher index creation statement."""
        props = ", ".join(f"n.{p}" for p in self.properties)

        if self.index_type == "btree":
            return (
                f"CREATE INDEX {self.name} "
                f"IF NOT EXISTS "
                f"FOR (n:{self.entity_type}) "
                f"ON ({props})"
            )
        elif self.index_type == "fulltext":
            return (
                f"CREATE FULLTEXT INDEX {self.name} "
                f"IF NOT EXISTS "
                f"FOR (n:{self.entity_type}) "
                f"ON EACH [{props}]"
            )
        elif self.index_type == "vector":
            # Vector index only supports single property
            return (
                f"CREATE VECTOR INDEX {self.name} "
                f"IF NOT EXISTS "
                f"FOR (n:{self.entity_type}) "
                f"ON (n.{self.properties[0]}) "
                f"OPTIONS {{indexConfig: {{`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}}}}"
            )
        elif self.index_type == "lookup":
            return f"CREATE LOOKUP INDEX {self.name} IF NOT EXISTS FOR (n) ON EACH labels(n)"
        return ""

    @property
    def drop_cypher(self) -> str:
        """Generate Cypher index drop statement."""
        return f"DROP INDEX {self.name} IF EXISTS"


# Entity types in the Value Fabric ontology (from value_fabric_ontology_schema.py spec)
ENTITY_TYPES = [
    # Primary Business Concepts
    "Capability",
    "UseCase",
    "Persona",
    "ValueDriver",
    "ValueMetric",
    # Product & Solution Domain
    "Product",
    "Feature",
    "Service",
    "Solution",
    "Technology",
    # Organizational Context
    "Organization",
    "BusinessUnit",
    "Process",
    "Activity",
    # Industry Reference Model Mappings
    "APQCProcess",
    "BIANServiceDomain",
    "FIBOEntity",
    # Supporting Concepts
    "Industry",
    "MarketSegment",
    "Geography",
    "Regulation",
    # Metadata & Provenance
    "DataSource",
    "ExtractionEvent",
    "ConfidenceScore",
    # Phase 2 Extensions
    "ValuePack",
    "Variable",
    "BenchmarkDataset",
]

# Relationship types (aligned with value_fabric_ontology_schema.py spec)
RELATIONSHIP_TYPES = [
    # Capability Relationships
    "enables",  # Capability -> UseCase (was ENABLES)
    "requires",  # Capability -> Capability / UseCase -> Feature
    "subTypeOf",  # Capability -> Capability (hierarchy)
    "implementedBy",  # Capability -> Feature
    "measuredBy",  # Capability -> ValueMetric
    # Use Case Relationships
    "delivers",  # UseCase -> ValueDriver
    "involves",  # UseCase -> Persona (was BENEFITS)
    "requiresFeature",  # UseCase -> Feature
    "partOf",  # UseCase -> Process
    # Value Relationships
    "impacts",  # ValueDriver -> ValueMetric
    "drivenBy",  # ValueDriver -> UseCase
    "measures",  # ValueMetric -> Any
    # Product Relationships
    "implements",  # Feature -> Capability
    "hasFeature",  # Product -> Feature
    "addresses",  # Product -> UseCase
    "provides",  # Service -> Capability
    # Persona Relationships
    "performs",  # Persona -> UseCase
    "benefitsFrom",  # Persona -> ValueDriver
    "belongsTo",  # Persona -> Organization
    # Organizational Relationships
    "contains",  # Process -> Activity
    "operatesIn",  # Organization -> Industry/Geography
    "owns",  # BusinessUnit -> Process
    # Reference Model Mappings
    "mapsToAPQC",  # Process/Activity/Capability -> APQCProcess
    "mapsToBIAN",  # Capability/Service -> BIANServiceDomain
    "mapsToFIBO",  # Organization -> FIBOEntity
    "semanticallyEquivalent",  # Any -> Any (coreference)
    # Provenance Relationships
    "extractedFrom",  # Any -> DataSource
    "generatedBy",  # Any -> ExtractionEvent
    "validatedBy",  # Any -> Agent
    "supersedes",  # Entity -> Entity (versioning)
    # Phase 2: Value Pack Relationships
    "hasDriver",  # ValuePack -> ValueDriver
    "hasFormula",  # ValuePack -> Formula
    "hasBenchmark",  # ValuePack -> BenchmarkDataset
    "belongsToPack",  # Variable/Formula -> ValuePack
    "usedIn",  # Variable -> Formula
    "dependsOn",  # Formula -> Formula
]

# Current retrieval set for vector similarity search.
# Keep this list aligned with src/retrieval/vector_store.py VECTOR_ENTITY_TYPES.
VECTOR_INDEX_ENTITY_TYPES = [
    "Capability",
    "UseCase",
    "Persona",
    "ValueDriver",
]

# Constraints for data integrity
CONSTRAINTS: list[Constraint] = [
    # Unique constraints on entity IDs
    Constraint("capability_id", "Capability", "id", "unique"),
    Constraint("usecase_id", "UseCase", "id", "unique"),
    Constraint("persona_id", "Persona", "id", "unique"),
    Constraint("valuedriver_id", "ValueDriver", "id", "unique"),
    Constraint("valuemetric_id", "ValueMetric", "id", "unique"),
    Constraint("product_id", "Product", "id", "unique"),
    Constraint("feature_id", "Feature", "id", "unique"),
    Constraint("service_id", "Service", "id", "unique"),
    Constraint("solution_id", "Solution", "id", "unique"),
    Constraint("technology_id", "Technology", "id", "unique"),
    Constraint("organization_id", "Organization", "id", "unique"),
    Constraint("businessunit_id", "BusinessUnit", "id", "unique"),
    Constraint("process_id", "Process", "id", "unique"),
    Constraint("activity_id", "Activity", "id", "unique"),
    Constraint("apqcprocess_id", "APQCProcess", "id", "unique"),
    Constraint("bianservicedomain_id", "BIANServiceDomain", "id", "unique"),
    Constraint("fiboentity_id", "FIBOEntity", "id", "unique"),
    Constraint("industry_id", "Industry", "id", "unique"),
    Constraint("marketsegment_id", "MarketSegment", "id", "unique"),
    Constraint("geography_id", "Geography", "id", "unique"),
    Constraint("regulation_id", "Regulation", "id", "unique"),
    Constraint("datasource_id", "DataSource", "id", "unique"),
    Constraint("extractionevent_id", "ExtractionEvent", "id", "unique"),
    Constraint("confidencescore_id", "ConfidenceScore", "id", "unique"),
    # Phase 2: Value Pack and Variable constraints
    Constraint("valuepack_id", "ValuePack", "id", "unique"),
    Constraint("variable_id", "Variable", "id", "unique"),
    Constraint("benchmarkdataset_id", "BenchmarkDataset", "id", "unique"),
    # NOTE: Property existence constraints require Neo4j Enterprise Edition.
    # For Community Edition compatibility, we skip these and rely on:
    # 1. Application-level validation
    # 2. Full-text indexes for name search (not null enforcement)
    # 3. Required field validation in API models
]

# P0-03: Tenant isolation constraints (requires Neo4j Enterprise Edition)
# These enforce that tenant_id cannot be null on any entity
# For Community Edition, tenant_id validation is done at application level
TENANT_CONSTRAINTS: list[Constraint] = [
    Constraint("capability_tenant_id", "Capability", "tenant_id", "exists"),
    Constraint("usecase_tenant_id", "UseCase", "tenant_id", "exists"),
    Constraint("persona_tenant_id", "Persona", "tenant_id", "exists"),
    Constraint("valuedriver_tenant_id", "ValueDriver", "tenant_id", "exists"),
    Constraint("valuemetric_tenant_id", "ValueMetric", "tenant_id", "exists"),
    Constraint("product_tenant_id", "Product", "tenant_id", "exists"),
    Constraint("feature_tenant_id", "Feature", "tenant_id", "exists"),
    Constraint("service_tenant_id", "Service", "tenant_id", "exists"),
    Constraint("solution_tenant_id", "Solution", "tenant_id", "exists"),
    Constraint("technology_tenant_id", "Technology", "tenant_id", "exists"),
    Constraint("organization_tenant_id", "Organization", "tenant_id", "exists"),
    Constraint("businessunit_tenant_id", "BusinessUnit", "tenant_id", "exists"),
    Constraint("process_tenant_id", "Process", "tenant_id", "exists"),
    Constraint("activity_tenant_id", "Activity", "tenant_id", "exists"),
    Constraint("valuepack_tenant_id", "ValuePack", "tenant_id", "exists"),
    Constraint("variable_tenant_id", "Variable", "tenant_id", "exists"),
    Constraint("formula_tenant_id", "Formula", "tenant_id", "exists"),
]

# Indexes for query performance
INDEXES: list[Index] = [
    # B-tree indexes for filtering
    Index("capability_name_idx", "Capability", ["name"], "btree"),
    Index("capability_confidence_idx", "Capability", ["confidence"], "btree"),
    Index("capability_level_idx", "Capability", ["capabilityLevel"], "btree"),
    Index("usecase_name_idx", "UseCase", ["name"], "btree"),
    Index("usecase_confidence_idx", "UseCase", ["confidence"], "btree"),
    Index("usecase_criticality_idx", "UseCase", ["businessCriticality"], "btree"),
    Index("persona_name_idx", "Persona", ["name"], "btree"),  # Fixed: was "title"
    Index("persona_department_idx", "Persona", ["department"], "btree"),
    Index("persona_roletype_idx", "Persona", ["role_type"], "btree"),
    Index(
        "persona_roletype_idx2", "Persona", ["roleType"], "btree"
    ),  # camelCase variant
    Index("valuedriver_name_idx", "ValueDriver", ["name"], "btree"),
    Index("valuedriver_category_idx", "ValueDriver", ["category"], "btree"),
    Index("valuedriver_valuecategory_idx", "ValueDriver", ["valueCategory"], "btree"),
    Index("valuemetric_name_idx", "ValueMetric", ["name"], "btree"),
    Index("product_name_idx", "Product", ["name"], "btree"),
    Index("product_vendor_idx", "Product", ["vendor"], "btree"),
    Index("feature_name_idx", "Feature", ["name"], "btree"),
    Index("apqcprocess_apqcid_idx", "APQCProcess", ["apqcId"], "btree"),
    Index("bianservicedomain_bianid_idx", "BIANServiceDomain", ["bianId"], "btree"),
    # Full-text indexes for search
    Index("capability_fulltext", "Capability", ["name", "description"], "fulltext"),
    Index("usecase_fulltext", "UseCase", ["name", "description"], "fulltext"),
    Index(
        "persona_fulltext", "Persona", ["name", "description", "department"], "fulltext"
    ),  # Fixed
    Index("valuedriver_fulltext", "ValueDriver", ["name", "description"], "fulltext"),
    Index("valuemetric_fulltext", "ValueMetric", ["name", "description"], "fulltext"),
    Index("product_fulltext", "Product", ["name", "description"], "fulltext"),
    Index("feature_fulltext", "Feature", ["name", "description"], "fulltext"),
    # Vector indexes for current retrieval entities.
    Index("capability_embedding_idx", "Capability", ["embedding"], "vector"),
    Index("usecase_embedding_idx", "UseCase", ["embedding"], "vector"),
    Index("persona_embedding_idx", "Persona", ["embedding"], "vector"),
    Index("valuedriver_embedding_idx", "ValueDriver", ["embedding"], "vector"),
    # Lookup index for efficient label scanning
    Index("entity_lookup", "", [], "lookup"),
    # Phase 2: Value Pack and Variable indexes
    Index("valuepack_name_idx", "ValuePack", ["name"], "btree"),
    Index("valuepack_industry_idx", "ValuePack", ["industry"], "btree"),
    Index("valuepack_status_idx", "ValuePack", ["status"], "btree"),
    Index("valuepack_fulltext", "ValuePack", ["name", "description"], "fulltext"),
    Index("variable_name_idx", "Variable", ["name"], "btree"),
    Index("variable_datatype_idx", "Variable", ["dataType"], "btree"),
    Index("variable_industry_idx", "Variable", ["industry"], "btree"),
    Index("variable_fulltext", "Variable", ["name", "description"], "fulltext"),
    Index("benchmarkdataset_name_idx", "BenchmarkDataset", ["name"], "btree"),
    Index("benchmarkdataset_industry_idx", "BenchmarkDataset", ["industry"], "btree"),
]

# Schema initialization order
SCHEMA_INIT_ORDER = [
    "constraints",
    "indexes",
    "entity_labels",
    "relationship_types",
]


def get_all_constraints() -> list[Constraint]:
    """Get all schema constraints."""
    return CONSTRAINTS


def get_tenant_constraints() -> list[Constraint]:
    """Get tenant isolation constraints (P0-03).

    These require Neo4j Enterprise Edition. Returns empty list for
    Community Edition compatibility.
    """
    return TENANT_CONSTRAINTS


def get_all_constraints_with_tenant(include_tenant: bool = False) -> list[Constraint]:
    """Get all constraints, optionally including tenant constraints.

    Args:
        include_tenant: If True, includes TENANT_CONSTRAINTS (Enterprise only)

    Returns:
        Combined list of constraints
    """
    if include_tenant:
        return CONSTRAINTS + TENANT_CONSTRAINTS
    return CONSTRAINTS


def get_all_indexes() -> list[Index]:
    """Get all schema indexes."""
    return INDEXES


def get_entity_types() -> list[str]:
    """Get all entity types in the ontology."""
    return ENTITY_TYPES


def get_relationship_types() -> list[str]:
    """Get all relationship types in the ontology."""
    return RELATIONSHIP_TYPES
