"""Value Pack service interface for Layer 4 Agents.

Internal service interface for Value Pack composition and lifecycle.
Tightly coupled domain seam — uses code-level interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum


class PackStatus(str, Enum):
    """Value Pack lifecycle status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class ValueDriverRef:
    """Reference to a Value Driver within a pack."""
    driver_id: str
    name: str
    category: str
    weight: float = 1.0  # For aggregation


@dataclass
class FormulaRef:
    """Reference to a Formula within a pack."""
    formula_id: str
    name: str
    version: str
    variables: List[str]  # Required variable names


@dataclass
class BenchmarkRef:
    """Reference to a Benchmark dataset within a pack."""
    dataset_id: str
    metric: str
    industry: str


@dataclass
class ValuePack:
    """Value Pack domain model.
    
    Combines ontology slice, value drivers, formulas, benchmarks,
    and workflow templates for a specific industry/segment.
    """
    pack_id: str
    name: str
    description: str
    industry: str
    segment: Optional[str]
    status: PackStatus
    version: str
    
    # Composition
    value_drivers: List[ValueDriverRef] = field(default_factory=list)
    formulas: List[FormulaRef] = field(default_factory=list)
    benchmarks: List[BenchmarkRef] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    
    # Runtime
    is_loaded: bool = False
    workspace_id: Optional[str] = None


@dataclass
class PackExecutionRequest:
    """Request to execute a Value Pack workflow."""
    pack_id: str
    workspace_id: str
    variables: Dict[str, Any]  # Variable bindings
    user_id: Optional[str] = None


@dataclass
class PackExecutionResult:
    """Result of Value Pack execution."""
    execution_id: str
    pack_id: str
    status: str  # success, partial, failed
    outputs: Dict[str, Any]  # Formula results, benchmarks, etc.
    errors: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class IValuePackService(ABC):
    """Abstract interface for Value Pack service.
    
    Internal service interface for pack composition and execution.
    Implementation is in-process (not HTTP) due to tight coupling
    with formula evaluation and workflow orchestration.
    """
    
    @abstractmethod
    async def list_packs(
        self,
        industry: Optional[str] = None,
        status: Optional[PackStatus] = None,
    ) -> List[ValuePack]:
        """List available Value Packs."""
        pass
    
    @abstractmethod
    async def get_pack(self, pack_id: str) -> Optional[ValuePack]:
        """Retrieve Value Pack by ID."""
        pass
    
    @abstractmethod
    async def load_pack_into_workspace(
        self,
        pack_id: str,
        workspace_id: str,
    ) -> ValuePack:
        """Load pack into workspace for customization/execution."""
        pass
    
    @abstractmethod
    async def execute_pack(
        self,
        request: PackExecutionRequest,
    ) -> PackExecutionResult:
        """Execute pack workflow with provided variables."""
        pass
    
    @abstractmethod
    async def customize_pack(
        self,
        pack_id: str,
        workspace_id: str,
        modifications: Dict[str, Any],
    ) -> ValuePack:
        """Fork and customize pack for account-specific needs."""
        pass
    
    @abstractmethod
    async def save_pack(
        self,
        pack: ValuePack,
    ) -> ValuePack:
        """Save pack (create new version or update draft)."""
        pass
