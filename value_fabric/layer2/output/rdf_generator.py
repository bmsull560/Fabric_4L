"""RDF/OWL output generation for Knowledge Graph serialization.

Stage 6 of the extraction pipeline: Converts extracted entities and relationships
to Turtle format with PROV-O provenance annotations.
"""

from datetime import datetime

from rdflib import OWL, RDF, RDFS, Graph, Literal, Namespace, URIRef
from rdflib.namespace import XSD

from layer2_extraction.models import (
    Capability,
    ExtractionResult,
    Feature,
    Persona,
    PredicateType,
    Relationship,
    UseCase,
    ValueDriver,
)

# Namespaces
VF = Namespace("http://valuefabric.io/ontology#")
PROV = Namespace("http://www.w3.org/ns/prov#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
APQC = Namespace("http://www.apqc.org/pcf#")


class RDFGenerator:
    """Generate RDF/OWL triples from extracted entities.

    Outputs Turtle format with:
    - OWL class definitions
    - Entity instances with properties
    - Relationships between entities
    - PROV-O provenance annotations
    """

    def __init__(self):
        """Initialize RDF generator with graph and namespaces."""
        self.graph = Graph()
        self._bind_namespaces()

    def _bind_namespaces(self) -> None:
        """Bind namespace prefixes for readable Turtle output."""
        self.graph.bind("vf", VF)
        self.graph.bind("prov", PROV)
        self.graph.bind("skos", SKOS)
        self.graph.bind("apqc", APQC)
        self.graph.bind("xsd", XSD)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("owl", OWL)

    def generate(self, result: ExtractionResult, relationships: list[Relationship]) -> str:
        """Generate RDF/Turtle from extraction result.

        Args:
            result: Extraction result with entities
            relationships: List of relationships

        Returns:
            Turtle format RDF string
        """
        # Add ontology definitions
        self._add_ontology_definitions()

        # Add entities
        for capability in result.capabilities:
            self._add_capability(capability)

        for use_case in result.use_cases:
            self._add_use_case(use_case)

        for persona in result.personas:
            self._add_persona(persona)

        for value_driver in result.value_drivers:
            self._add_value_driver(value_driver)

        # Add features
        for feature in result.features:
            self._add_feature(feature)

        # Add relationships
        for relationship in relationships:
            self._add_relationship(relationship)

        # Serialize to Turtle
        return self.graph.serialize(format="turtle")

    def _add_ontology_definitions(self) -> None:
        """Add OWL class definitions to graph."""
        # Capability class
        self.graph.add((VF.Capability, RDF.type, OWL.Class))
        self.graph.add((VF.Capability, RDFS.label, Literal("Capability")))
        self.graph.add(
            (
                VF.Capability,
                RDFS.comment,
                Literal("A technical capability or feature of a product/service"),
            )
        )

        # UseCase class
        self.graph.add((VF.UseCase, RDF.type, OWL.Class))
        self.graph.add((VF.UseCase, RDFS.label, Literal("Use Case")))

        # Persona class
        self.graph.add((VF.Persona, RDF.type, OWL.Class))
        self.graph.add((VF.Persona, RDFS.label, Literal("Persona")))

        # ValueDriver class
        self.graph.add((VF.ValueDriver, RDF.type, OWL.Class))
        self.graph.add((VF.ValueDriver, RDFS.label, Literal("Value Driver")))

        # Feature class
        self.graph.add((VF.Feature, RDF.type, OWL.Class))
        self.graph.add((VF.Feature, RDFS.label, Literal("Feature")))
        self.graph.add(
            (VF.Feature, RDFS.comment, Literal("A product feature that implements a capability"))
        )

        # Predicate properties (as OWL ObjectProperties)
        predicates = [
            (VF.enables, "enables", "Capability enables UseCase"),
            (VF.requires, "requires", "UseCase requires Capability"),
            (VF.benefits, "benefits", "UseCase benefits Persona"),
            (VF.drives, "drives", "Persona drives ValueDriver"),
            (VF.contributesTo, "contributes_to", "Capability contributes to ValueDriver"),
            (VF.dependsOn, "depends_on", "Capability depends on Capability"),
            (VF.alternativeTo, "alternative_to", "Capability is alternative to Capability"),
            # Extended predicates
            (VF.capabilitySubtypeOf, "capability_subtype_of", "Capability is subtype of another"),
            (
                VF.capabilityRequiresCapability,
                "capability_requires_capability",
                "Capability requires another capability",
            ),
            (
                VF.semanticallyEquivalent,
                "semantically_equivalent",
                "Entities are semantically equivalent",
            ),
            (VF.implements, "implements", "Feature implements a capability"),
            (VF.delivers, "delivers", "UseCase delivers value"),
            (VF.involves, "involves", "UseCase involves persona"),
        ]

        for uri, label, comment in predicates:
            self.graph.add((uri, RDF.type, OWL.ObjectProperty))
            self.graph.add((uri, RDFS.label, Literal(label)))
            self.graph.add((uri, RDFS.comment, Literal(comment)))

    def _add_capability(self, capability: Capability) -> None:
        """Add a Capability instance to graph."""
        uri = URIRef(f"http://valuefabric.io/entity/{capability.id}")

        # Type
        self.graph.add((uri, RDF.type, VF.Capability))

        # Properties
        self.graph.add((uri, VF.name, Literal(capability.name)))
        self.graph.add((uri, VF.description, Literal(capability.description)))
        self.graph.add((uri, VF.confidence, Literal(capability.confidence, datatype=XSD.float)))

        # Technical features
        for feature in capability.technical_features:
            self.graph.add((uri, VF.technicalFeature, Literal(feature)))

        # API endpoints
        for endpoint in capability.api_endpoints:
            self.graph.add((uri, VF.apiEndpoint, Literal(endpoint)))

        # Integrations
        for integration in capability.integrations:
            self.graph.add((uri, VF.integration, Literal(integration)))

        # APQC mapping
        if capability.apqc_mapping:
            self.graph.add((uri, SKOS.closeMatch, APQC[capability.apqc_mapping]))

        # Source references
        for source in capability.source_refs:
            self.graph.add((uri, VF.sourceUrl, Literal(source)))

        # Provenance
        self._add_provenance(uri, capability.extraction_job_id, capability.extracted_at)

    def _add_use_case(self, use_case: UseCase) -> None:
        """Add a UseCase instance to graph."""
        uri = URIRef(f"http://valuefabric.io/entity/{use_case.id}")

        self.graph.add((uri, RDF.type, VF.UseCase))
        self.graph.add((uri, VF.name, Literal(use_case.name)))
        self.graph.add((uri, VF.description, Literal(use_case.description)))
        self.graph.add((uri, VF.confidence, Literal(use_case.confidence, datatype=XSD.float)))

        # Industry context
        for industry in use_case.industry_context:
            self.graph.add((uri, VF.industry, Literal(industry)))

        # Workflow steps
        for i, step in enumerate(use_case.workflow_steps):
            self.graph.add((uri, VF.workflowStep, Literal(f"{i + 1}. {step}")))

        # KPIs
        for kpi in use_case.kpis:
            self.graph.add((uri, VF.kpi, Literal(kpi)))

        # Required capabilities (links added via relationships)

        self._add_provenance(uri, use_case.extraction_job_id, use_case.extracted_at)

    def _add_persona(self, persona: Persona) -> None:
        """Add a Persona instance to graph."""
        uri = URIRef(f"http://valuefabric.io/entity/{persona.id}")

        self.graph.add((uri, RDF.type, VF.Persona))
        role_type_value = getattr(persona.role_type, "value", persona.role_type)
        self.graph.add((uri, VF.roleType, Literal(role_type_value)))

        # Seniority level (new field)
        seniority_value = getattr(persona.seniority_level, "value", persona.seniority_level)
        self.graph.add((uri, VF.seniorityLevel, Literal(seniority_value)))

        self.graph.add((uri, VF.title, Literal(persona.title)))
        self.graph.add((uri, VF.department, Literal(persona.department)))
        self.graph.add((uri, VF.confidence, Literal(persona.confidence, datatype=XSD.float)))

        # Pain points
        for pain in persona.pain_points:
            self.graph.add((uri, VF.painPoint, Literal(pain)))

        # Success metrics
        for metric in persona.success_metrics:
            self.graph.add((uri, VF.successMetric, Literal(metric)))

        self._add_provenance(uri, persona.extraction_job_id, persona.extracted_at)

    def _add_value_driver(self, value_driver: ValueDriver) -> None:
        """Add a ValueDriver instance to graph."""
        uri = URIRef(f"http://valuefabric.io/entity/{value_driver.id}")

        self.graph.add((uri, RDF.type, VF.ValueDriver))
        category_value = getattr(value_driver.category, "value", value_driver.category)
        self.graph.add((uri, VF.category, Literal(category_value)))
        self.graph.add((uri, VF.name, Literal(value_driver.name)))
        self.graph.add((uri, VF.description, Literal(value_driver.description)))
        self.graph.add((uri, VF.unit, Literal(value_driver.unit)))
        self.graph.add((uri, VF.confidence, Literal(value_driver.confidence, datatype=XSD.float)))

        # Metrics
        for metric in value_driver.metrics:
            self.graph.add((uri, VF.metric, Literal(metric)))

        # Formula
        if value_driver.formula_string:
            self.graph.add((uri, VF.formulaString, Literal(value_driver.formula_string)))

        # Time to value
        if value_driver.time_to_value:
            self.graph.add((uri, VF.timeToValue, Literal(value_driver.time_to_value)))

        self._add_provenance(uri, value_driver.extraction_job_id, value_driver.extracted_at)

    def _add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship between entities."""
        source_uri = URIRef(f"http://valuefabric.io/entity/{relationship.source_id}")
        target_uri = URIRef(f"http://valuefabric.io/entity/{relationship.target_id}")

        # Map predicate type to VF property
        predicate_map = {
            PredicateType.ENABLES: VF.enables,
            PredicateType.REQUIRES: VF.requires,
            PredicateType.BENEFITS: VF.benefits,
            PredicateType.DRIVES: VF.drives,
            PredicateType.CONTRIBUTES_TO: VF.contributesTo,
            PredicateType.DEPENDS_ON: VF.dependsOn,
            PredicateType.ALTERNATIVE_TO: VF.alternativeTo,
            # Extended predicates
            PredicateType.CAPABILITY_SUBTYPE_OF: VF.capabilitySubtypeOf,
            PredicateType.CAPABILITY_REQUIRES_CAPABILITY: VF.capabilityRequiresCapability,
            PredicateType.SEMANTICALLY_EQUIVALENT: VF.semanticallyEquivalent,
            PredicateType.IMPLEMENTS: VF.implements,
            PredicateType.DELIVERS: VF.delivers,
            PredicateType.INVOLVES: VF.involves,
        }

        predicate = predicate_map.get(relationship.canonical_predicate)
        if predicate:
            # Add the relationship
            self.graph.add((source_uri, predicate, target_uri))

            # Add reified statement for properties
            statement = URIRef(f"http://valuefabric.io/relationship/{relationship.id}")
            self.graph.add((statement, RDF.type, RDF.Statement))
            self.graph.add((statement, RDF.subject, source_uri))
            self.graph.add((statement, RDF.predicate, predicate))
            self.graph.add((statement, RDF.object, target_uri))

            # Store raw predicate (preserves extraction richness)
            self.graph.add((statement, VF.rawPredicate, Literal(relationship.raw_predicate)))

            # Relationship properties
            self.graph.add(
                (statement, VF.confidence, Literal(relationship.confidence, datatype=XSD.float))
            )
            self.graph.add((statement, VF.evidenceText, Literal(relationship.evidence_text)))
            self.graph.add((statement, VF.sourceUrl, Literal(relationship.source_url)))

            if relationship.impact_level:
                self.graph.add(
                    (statement, VF.impactLevel, Literal(relationship.impact_level.value))
                )

            if relationship.strength:
                self.graph.add(
                    (statement, VF.strength, Literal(relationship.strength, datatype=XSD.float))
                )

            # New relationship properties (best-effort extraction)
            if relationship.enablement_type:
                self.graph.add(
                    (statement, VF.enablementType, Literal(relationship.enablement_type.value))
                )

            if relationship.benefit_type:
                self.graph.add(
                    (statement, VF.benefitType, Literal(relationship.benefit_type.value))
                )

            if relationship.driver_type:
                self.graph.add(
                    (statement, VF.driverType, Literal(relationship.driver_type.value))
                )

            if relationship.contribution_weight is not None:
                self.graph.add(
                    (statement, VF.contributionWeight, Literal(relationship.contribution_weight, datatype=XSD.float))
                )

            if relationship.influence_weight is not None:
                self.graph.add(
                    (statement, VF.influenceWeight, Literal(relationship.influence_weight, datatype=XSD.float))
                )

            # Provenance
            self._add_provenance(
                statement, relationship.extraction_job_id, relationship.extracted_at
            )

    def _add_feature(self, feature: Feature) -> None:
        """Add a Feature instance to graph."""
        uri = URIRef(f"http://valuefabric.io/entity/{feature.id}")

        self.graph.add((uri, RDF.type, VF.Feature))
        self.graph.add((uri, VF.name, Literal(feature.name)))
        self.graph.add((uri, VF.description, Literal(feature.description)))
        self.graph.add((uri, VF.implementationStatus, Literal(feature.implementation_status)))
        self.graph.add((uri, VF.confidence, Literal(feature.confidence, datatype=XSD.float)))

        # Technical spec
        if feature.technical_spec:
            self.graph.add((uri, VF.technicalSpec, Literal(feature.technical_spec)))

        # Parent capability link
        if feature.parent_capability_id:
            parent_uri = URIRef(f"http://valuefabric.io/entity/{feature.parent_capability_id}")
            self.graph.add((uri, VF.implements, parent_uri))

        # Source references
        for source in feature.source_refs:
            self.graph.add((uri, VF.sourceUrl, Literal(source)))

        self._add_provenance(uri, feature.extraction_job_id, feature.extracted_at)

    def _add_provenance(self, uri: URIRef, job_id: str | None, timestamp: datetime) -> None:
        """Add PROV-O provenance annotations."""
        # Entity was generated by extraction activity
        if job_id:
            activity = URIRef(f"http://valuefabric.io/activity/{job_id}")
            self.graph.add((uri, PROV.wasGeneratedBy, activity))

        # Extraction timestamp
        timestamp_str = timestamp.isoformat()
        self.graph.add((uri, PROV.generatedAtTime, Literal(timestamp_str, datatype=XSD.dateTime)))

        # Entity type (for type-based queries)
        self.graph.add((uri, RDF.type, PROV.Entity))


def generate_rdf(result: ExtractionResult, relationships: list[Relationship]) -> str:
    """Convenience function to generate RDF.

    Args:
        result: Extraction result with entities
        relationships: List of relationships

    Returns:
        Turtle format RDF string
    """
    generator = RDFGenerator()
    return generator.generate(result, relationships)
