"""Default ontology schema seed data.

Provides the initial ontology types and relationships for new tenants.
This matches the extraction capabilities defined in the LLM prompts.
"""

from layer2_extraction.models.ontology import (
    Cardinality,
    OntologyProperty,
    OntologySchema,
    OntologyType,
    PropertyConstraints,
    PropertyType,
    RelationshipType,
    TypeRelationship,
)


def get_default_ontology_schema() -> OntologySchema:
    """Get the default ontology schema for new tenants.

    This schema defines the core entity types that the extraction pipeline
    can identify and extract from source documents.
    """
    types: list[OntologyType] = [
        OntologyType(
            id="capability",
            name="Capability",
            description="A technical capability or feature of a product/service",
            properties=[
                OntologyProperty(
                    id="cap-name",
                    name="name",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(min_length=1, max_length=255),
                ),
                OntologyProperty(
                    id="cap-desc",
                    name="description",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(min_length=10),
                ),
                OntologyProperty(
                    id="cap-features",
                    name="technical_features",
                    type=PropertyType.ARRAY,
                    required=False,
                ),
                OntologyProperty(
                    id="cap-api",
                    name="api_endpoints",
                    type=PropertyType.ARRAY,
                    required=False,
                ),
                OntologyProperty(
                    id="cap-integrations",
                    name="integrations",
                    type=PropertyType.ARRAY,
                    required=False,
                ),
                OntologyProperty(
                    id="cap-apqc",
                    name="apqc_mapping",
                    type=PropertyType.STRING,
                    required=False,
                ),
                OntologyProperty(
                    id="cap-confidence",
                    name="confidence",
                    type=PropertyType.NUMBER,
                    required=True,
                    constraints=PropertyConstraints(min=0, max=1),
                ),
            ],
            children_type_ids=["feature"],
        ),
        OntologyType(
            id="feature",
            name="Feature",
            description="A product feature that implements a capability",
            parent_type_id="capability",
            properties=[
                OntologyProperty(
                    id="feat-name",
                    name="name",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(min_length=1, max_length=255),
                ),
                OntologyProperty(
                    id="feat-desc",
                    name="description",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(min_length=10),
                ),
                OntologyProperty(
                    id="feat-parent",
                    name="parent_capability_id",
                    type=PropertyType.REFERENCE,
                    required=False,
                    constraints=PropertyConstraints(reference_type_id="capability"),
                ),
                OntologyProperty(
                    id="feat-status",
                    name="implementation_status",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(enum=["planned", "beta", "ga", "deprecated"]),
                ),
                OntologyProperty(
                    id="feat-confidence",
                    name="confidence",
                    type=PropertyType.NUMBER,
                    required=True,
                    constraints=PropertyConstraints(min=0, max=1),
                ),
            ],
        ),
        OntologyType(
            id="usecase",
            name="UseCase",
            description="A business use case that solves a specific problem",
            properties=[
                OntologyProperty(
                    id="uc-name",
                    name="name",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(min_length=1, max_length=255),
                ),
                OntologyProperty(
                    id="uc-desc",
                    name="description",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(min_length=10),
                ),
                OntologyProperty(
                    id="uc-industry",
                    name="industry_context",
                    type=PropertyType.ARRAY,
                    required=False,
                ),
                OntologyProperty(
                    id="uc-caps",
                    name="required_capabilities",
                    type=PropertyType.ARRAY,
                    required=False,
                ),
                OntologyProperty(
                    id="uc-workflow",
                    name="workflow_steps",
                    type=PropertyType.ARRAY,
                    required=False,
                ),
                OntologyProperty(
                    id="uc-kpis",
                    name="kpis",
                    type=PropertyType.ARRAY,
                    required=False,
                ),
                OntologyProperty(
                    id="uc-confidence",
                    name="confidence",
                    type=PropertyType.NUMBER,
                    required=True,
                    constraints=PropertyConstraints(min=0, max=1),
                ),
            ],
        ),
        OntologyType(
            id="persona",
            name="Persona",
            description="A stakeholder or user persona in the enterprise buying process",
            properties=[
                OntologyProperty(
                    id="per-role",
                    name="role_type",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(
                        enum=["economic_buyer", "champion", "operational_user", "technical_buyer", "stakeholder"]
                    ),
                ),
                OntologyProperty(
                    id="per-seniority",
                    name="seniority_level",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(
                        enum=["executive_sponsor", "c_suite", "vp", "director", "manager", "individual_contributor", "unknown"]
                    ),
                ),
                OntologyProperty(
                    id="per-title",
                    name="title",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(min_length=1, max_length=255),
                ),
                OntologyProperty(
                    id="per-dept",
                    name="department",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(min_length=1, max_length=255),
                ),
                OntologyProperty(
                    id="per-pain",
                    name="pain_points",
                    type=PropertyType.ARRAY,
                    required=False,
                ),
                OntologyProperty(
                    id="per-metrics",
                    name="success_metrics",
                    type=PropertyType.ARRAY,
                    required=False,
                ),
                OntologyProperty(
                    id="per-influenced",
                    name="influenced_by",
                    type=PropertyType.ARRAY,
                    required=False,
                ),
                OntologyProperty(
                    id="per-confidence",
                    name="confidence",
                    type=PropertyType.NUMBER,
                    required=True,
                    constraints=PropertyConstraints(min=0, max=1),
                ),
            ],
        ),
        OntologyType(
            id="valuedriver",
            name="ValueDriver",
            description="A quantifiable business value that drives ROI",
            properties=[
                OntologyProperty(
                    id="vd-category",
                    name="category",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(
                        enum=["capital_efficiency", "cost_reduction", "risk_mitigation", "revenue_enhancement"]
                    ),
                ),
                OntologyProperty(
                    id="vd-name",
                    name="name",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(min_length=1, max_length=255),
                ),
                OntologyProperty(
                    id="vd-desc",
                    name="description",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(min_length=10),
                ),
                OntologyProperty(
                    id="vd-metrics",
                    name="metrics",
                    type=PropertyType.ARRAY,
                    required=False,
                ),
                OntologyProperty(
                    id="vd-formula",
                    name="formula_string",
                    type=PropertyType.STRING,
                    required=False,
                ),
                OntologyProperty(
                    id="vd-unit",
                    name="unit",
                    type=PropertyType.STRING,
                    required=True,
                    constraints=PropertyConstraints(min_length=1, max_length=50),
                ),
                OntologyProperty(
                    id="vd-ttv",
                    name="time_to_value",
                    type=PropertyType.STRING,
                    required=False,
                ),
                OntologyProperty(
                    id="vd-confidence",
                    name="confidence",
                    type=PropertyType.NUMBER,
                    required=True,
                    constraints=PropertyConstraints(min=0, max=1),
                ),
            ],
        ),
    ]

    relationships: list[TypeRelationship] = [
        TypeRelationship(
            id="rel-capability-feature",
            source_type_id="feature",
            target_type_id="capability",
            relationship_type=RelationshipType.EXTENDS,
            description="Feature implements a capability",
            cardinality=Cardinality.MANY_TO_MANY,
        ),
        TypeRelationship(
            id="rel-usecase-capability",
            source_type_id="usecase",
            target_type_id="capability",
            relationship_type=RelationshipType.DEPENDS_ON,
            description="Use case requires capabilities",
            cardinality=Cardinality.MANY_TO_MANY,
        ),
        TypeRelationship(
            id="rel-valuedriver-usecase",
            source_type_id="valuedriver",
            target_type_id="usecase",
            relationship_type=RelationshipType.RELATES_TO,
            description="Value driver relates to use cases",
            cardinality=Cardinality.ONE_TO_MANY,
        ),
        TypeRelationship(
            id="rel-persona-usecase",
            source_type_id="persona",
            target_type_id="usecase",
            relationship_type=RelationshipType.RELATES_TO,
            description="Persona participates in use cases",
            cardinality=Cardinality.MANY_TO_MANY,
        ),
    ]

    return OntologySchema(
        types=types,
        relationships=relationships,
        version="1.0.0",
    )


async def seed_default_ontology(tenant_id: str, repo) -> OntologySchema:
    """Seed the default ontology schema for a new tenant.

    Args:
        tenant_id: The tenant ID to seed
        repo: OntologySchemaRepository instance

    Returns:
        The seeded ontology schema
    """
    schema = get_default_ontology_schema()
    return await repo.import_schema(tenant_id, schema, "system")
