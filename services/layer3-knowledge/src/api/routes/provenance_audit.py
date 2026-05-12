"""Allowed service-local exception for Layer 3 service wrapper.

Owner: layer3-knowledge
Removal/migration target: 2026-09-30
Reason: Service-wrapper-only logic permitted by runtime path governance.
"""


from value_fabric.layer3.api.routes.provenance_audit import *  # noqa: F401,F403
