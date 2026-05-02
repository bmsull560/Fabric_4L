"""Seed data for Layer 2 Extraction.

Provides default ontology schema for new tenants.
"""

from .ontology_seed import get_default_ontology_schema, seed_default_ontology

__all__ = ["seed_default_ontology", "get_default_ontology_schema"]
