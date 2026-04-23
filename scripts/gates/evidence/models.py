"""Evidence models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4


class EvidenceCategory(Enum):
    """SOC2 evidence categories."""
    ACCESS_CONTROL = "access_control"
    CHANGE_MANAGEMENT = "change_management"
    SECURITY_OPERATIONS = "security_operations"
    AVAILABILITY = "availability"
    INCIDENT_RESPONSE = "incident_response"
    POLICIES = "policies"


@dataclass
class EvidenceItem:
    """Single piece of evidence."""
    path: Path
    content_type: str
    checksum: str
    size_bytes: int
    category: EvidenceCategory
    metadata: dict = field(default_factory=dict)


@dataclass
class EvidenceBundle:
    """Collection of evidence for a gate."""
    bundle_id: UUID = field(default_factory=uuid4)
    category: EvidenceCategory
    gate_id: str
    release_id: Optional[str] = None
    items: list[EvidenceItem] = field(default_factory=list)
    trace_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


@dataclass
class AuditBundle:
    """Complete audit bundle for compliance."""
    bundle_id: UUID = field(default_factory=uuid4)
    release_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    bundles: list[EvidenceBundle] = field(default_factory=list)
    manifest: dict = field(default_factory=dict)
    checksum: str = ""
