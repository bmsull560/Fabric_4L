"""Formula Governance interface for Layer 4 Agents.

Provides versioned, governed financial logic with activation lifecycle.
Internal interfaces for core operations, API contracts for management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timezone


class FormulaStatus(str, Enum):
    """Formula lifecycle status."""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass
class FormulaVersion:
    """Formula version metadata."""
    version: str  # semver
    formula_id: str
    status: FormulaStatus
    created_at: datetime
    created_by: str
    change_summary: str
    previous_version: Optional[str] = None


@dataclass
class FormulaGovernance:
    """Governance metadata for a formula."""
    formula_id: str
    current_version: str
    status: FormulaStatus
    
    # Version history
    versions: List[FormulaVersion] = field(default_factory=list)
    
    # Approval workflow
    approvers: List[str] = field(default_factory=list)
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    
    # Metadata
    owner: Optional[str] = None
    department: Optional[str] = None
    review_cycle_days: int = 90
    last_reviewed_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None


@dataclass
class FormulaDependency:
    """Dependency relationship between formulas."""
    source_formula_id: str
    target_formula_id: str
    dependency_type: str  # "uses", "extends", "validates"
    created_at: datetime = field(default_factory=datetime.now(timezone.utc))


@dataclass
class ActivationRequest:
    """Request to activate a formula version."""
    formula_id: str
    version: str
    requested_by: str
    justification: str
    effective_date: Optional[datetime] = None


@dataclass
class DeprecationRequest:
    """Request to deprecate a formula."""
    formula_id: str
    replacement_formula_id: Optional[str]
    deprecation_date: datetime
    reason: str
    requested_by: str


@dataclass
class GovernanceTransitionResult:
    """Result of governance state transition."""
    success: bool
    formula_id: str
    old_status: FormulaStatus
    new_status: FormulaStatus
    error_message: Optional[str] = None
    requires_approval: bool = False


class IFormulaGovernanceService(ABC):
    """Abstract interface for Formula Governance.
    
    Internal service interface for core governance operations.
    HTTP API exposed for administrative management.
    """
    
    @abstractmethod
    async def get_governance(self, formula_id: str) -> Optional[FormulaGovernance]:
        """Retrieve governance metadata for formula."""
        pass
    
    @abstractmethod
    async def create_version(
        self,
        formula_id: str,
        new_version: str,
        change_summary: str,
        created_by: str,
    ) -> FormulaVersion:
        """Create new formula version."""
        pass
    
    @abstractmethod
    async def list_versions(
        self,
        formula_id: str,
        include_retired: bool = False,
    ) -> List[FormulaVersion]:
        """List all versions of a formula."""
        pass
    
    @abstractmethod
    async def activate(
        self,
        request: ActivationRequest,
    ) -> GovernanceTransitionResult:
        """Activate a formula version."""
        pass
    
    @abstractmethod
    async def deprecate(
        self,
        request: DeprecationRequest,
    ) -> GovernanceTransitionResult:
        """Deprecate a formula."""
        pass
    
    @abstractmethod
    async def get_dependencies(
        self,
        formula_id: str,
        direction: str = "outgoing",  # outgoing, incoming, both
    ) -> List[FormulaDependency]:
        """Get formula dependencies."""
        pass
    
    @abstractmethod
    async def validate_activation(
        self,
        formula_id: str,
        version: str,
    ) -> Dict[str, Any]:
        """Validate if formula can be activated."""
        pass


class IFormulaApprovalWorkflow(ABC):
    """Interface for formula approval workflow.
    
    Admin-only transitions with audit trail.
    """
    
    @abstractmethod
    async def submit_for_review(
        self,
        formula_id: str,
        version: str,
        submitted_by: str,
    ) -> GovernanceTransitionResult:
        """Submit formula for review."""
        pass
    
    @abstractmethod
    async def approve(
        self,
        formula_id: str,
        version: str,
        approved_by: str,
        comments: Optional[str] = None,
    ) -> GovernanceTransitionResult:
        """Approve formula (admin only)."""
        pass
    
    @abstractmethod
    async def reject(
        self,
        formula_id: str,
        version: str,
        rejected_by: str,
        reason: str,
    ) -> GovernanceTransitionResult:
        """Reject formula (admin only)."""
        pass
