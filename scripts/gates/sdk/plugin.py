"""Gate plugin base class and execution context."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from uuid import UUID, uuid4

from .models import (
    GateArtifact,
    GateExecution,
    GatePolicy,
    GateProfile,
    GateResult,
    GateSeverity,
    CheckResult,
)


@dataclass
class GateContext:
    """Execution context passed to gates."""
    execution_id: UUID = field(default_factory=uuid4)
    gate_id: str = ""
    profile: GateProfile = GateProfile.PR_FAST
    policy: Optional[GatePolicy] = None
    workspace_dir: Path = field(default_factory=lambda: Path.cwd())
    output_dir: Path = field(default_factory=lambda: Path("artifacts"))
    trace_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)


class GatePlugin(ABC):
    """Base class for all gate plugins."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"gates.{self.gate_id}")
        self._execution: Optional[GateExecution] = None
    
    @property
    @abstractmethod
    def gate_id(self) -> str:
        """Unique gate identifier (e.g., 'arch', 'security')."""
        pass
    
    @property
    @abstractmethod
    def severity(self) -> GateSeverity:
        """Gate severity level."""
        pass
    
    @property
    @abstractmethod
    def expected_artifacts(self) -> list[str]:
        """List of artifact path patterns relative to gate output dir."""
        pass
    
    @abstractmethod
    def execute(self, ctx: GateContext) -> list[CheckResult]:
        """
        Execute gate checks.
        
        Args:
            ctx: Execution context with profile, policy, workspace
            
        Returns:
            List of check results for threshold evaluation
        """
        pass
    
    def setup(self, ctx: GateContext) -> None:
        """Setup before execution. Override for custom setup."""
        self._execution = GateExecution(
            gate_id=self.gate_id,
            profile=ctx.profile,
            trace_id=ctx.trace_id,
        )
        gate_output = ctx.output_dir / self.gate_id
        gate_output.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Setting up gate {self.gate_id} in {gate_output}")
    
    def teardown(self, ctx: GateContext, results: list[CheckResult]) -> None:
        """Cleanup after execution. Override for custom cleanup."""
        if self._execution:
            self._execution.finished_at = datetime.utcnow()
            self._execution.results = results
        self.logger.info(f"Gate {self.gate_id} completed with {len(results)} results")
    
    def collect_artifacts(self, output_dir: Path) -> list[GateArtifact]:
        """
        Collect and validate artifacts.
        
        Args:
            output_dir: Directory containing gate artifacts
            
        Returns:
            List of validated artifacts with checksums
        """
        import hashlib
        
        artifacts = []
        gate_output = output_dir / self.gate_id
        
        for pattern in self.expected_artifacts:
            for path in gate_output.glob(pattern):
                if path.is_file():
                    content = path.read_bytes()
                    checksum = hashlib.sha256(content).hexdigest()
                    
                    # Determine content type
                    content_type = "application/octet-stream"
                    if path.suffix == ".json":
                        content_type = "application/json"
                    elif path.suffix == ".md":
                        content_type = "text/markdown"
                    elif path.suffix in (".txt", ".log"):
                        content_type = "text/plain"
                    elif path.suffix == ".yaml" or path.suffix == ".yml":
                        content_type = "application/x-yaml"
                    
                    artifacts.append(GateArtifact(
                        path=path,
                        content_type=content_type,
                        checksum=checksum,
                        size_bytes=len(content),
                    ))
                    self.logger.debug(f"Collected artifact: {path} ({len(content)} bytes)")
        
        return artifacts
    
    def run(self, ctx: GateContext) -> GateExecution:
        """
        Full gate execution lifecycle.
        
        Args:
            ctx: Execution context
            
        Returns:
            Complete execution record with results and artifacts
        """
        from datetime import datetime
        
        self.setup(ctx)
        
        try:
            results = self.execute(ctx)
            self.teardown(ctx, results)
            
            # Collect artifacts
            artifacts = self.collect_artifacts(ctx.output_dir)
            if self._execution:
                self._execution.artifacts = artifacts
            
            return self._execution
            
        except Exception as e:
            self.logger.exception(f"Gate {self.gate_id} failed with error")
            error_result = CheckResult(
                name="gate_execution",
                result=GateResult.ERROR,
                message=str(e),
            )
            self.teardown(ctx, [error_result])
            
            if self._execution:
                self._execution.artifacts = self.collect_artifacts(ctx.output_dir)
            
            return self._execution


def datetime_now():
    """Helper to get current UTC datetime."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)
