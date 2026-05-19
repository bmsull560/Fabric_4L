"""Layer 2 API routes package."""

from layer2_extraction.api.routes import audit as audit_module
from layer2_extraction.api.routes import extraction as extraction_module
from layer2_extraction.api.routes import health as health_module
from layer2_extraction.api.routes import jobs as jobs_module
from layer2_extraction.api.routes import ontology as ontology_module
from layer2_extraction.api.routes import system as system_module

# Expose routers with names expected by app_factory.py
system = system_module
extraction = extraction_module
jobs = jobs_module
health = health_module
ontology = ontology_module
audit = audit_module

__all__ = [
    "audit",
    "extraction",
    "health",
    "jobs",
    "ontology",
    "system",
]
