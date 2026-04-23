"""Release manifest signing."""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from sdk.models import GateExecution, GateResult


@dataclass
class SignedManifest:
    """Signed release manifest."""
    manifest_version: str = "2.0"
    release_id: str = ""
    commit: str = ""
    branch: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    profile: str = ""
    gates: list[dict] = field(default_factory=list)
    verdict: dict = field(default_factory=dict)
    signatures: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class ManifestSigner:
    """Signs release manifests."""
    
    def __init__(self, key_id: str = "fabric-release-signing"):
        self.key_id = key_id
        self.logger = logging.getLogger("gated.signing")
    
    def create_manifest(
        self,
        release_id: str,
        commit: str,
        branch: str,
        profile: str,
        executions: list[GateExecution],
        verdict: dict,
    ) -> SignedManifest:
        """
        Create unsigned release manifest.
        
        Args:
            release_id: Release identifier
            commit: Git commit hash
            branch: Git branch
            profile: Release profile
            executions: List of gate executions
            verdict: Release verdict
            
        Returns:
            Unsigned manifest
        """
        gates = []
        
        for execution in executions:
            gate_data = {
                "gate_id": execution.gate_id,
                "result": execution.verdict.result.value if execution.verdict else "unknown",
                "duration_seconds": self._calculate_duration(execution),
                "artifacts": [
                    {
                        "path": str(a.path),
                        "checksum": a.checksum,
                        "size_bytes": a.size_bytes,
                    }
                    for a in execution.artifacts
                ],
                "checks": [
                    {
                        "name": r.name,
                        "result": r.result.value,
                        "value": r.value,
                        "threshold": r.threshold,
                    }
                    for r in execution.results
                ],
            }
            gates.append(gate_data)
        
        manifest = SignedManifest(
            release_id=release_id,
            commit=commit,
            branch=branch,
            profile=profile,
            gates=gates,
            verdict=verdict,
        )
        
        self.logger.info(f"Created manifest for {release_id}: {len(gates)} gates")
        
        return manifest
    
    def sign(self, manifest: SignedManifest) -> SignedManifest:
        """
        Sign manifest with configured key.
        
        Args:
            manifest: Manifest to sign
            
        Returns:
            Signed manifest
        
        Note:
            This is a base class. Use LocalKeySigner or KMSSigner for actual signing.
        """
        raise NotImplementedError("Subclasses must implement sign()")
    
    def verify(self, manifest: SignedManifest) -> bool:
        """
        Verify manifest signatures.
        
        Args:
            manifest: Manifest to verify
            
        Returns:
            True if signatures valid
        """
        raise NotImplementedError("Subclasses must implement verify()")
    
    def save(self, manifest: SignedManifest, path: Path) -> None:
        """Save manifest to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(manifest.to_json())
        self.logger.info(f"Saved manifest to {path}")
    
    def _calculate_duration(self, execution: GateExecution) -> float:
        """Calculate execution duration."""
        if execution.finished_at and execution.started_at:
            return (execution.finished_at - execution.started_at).total_seconds()
        return 0.0


class UnsignedManifestSigner(ManifestSigner):
    """Signer that creates unsigned manifests (for testing)."""
    
    def sign(self, manifest: SignedManifest) -> SignedManifest:
        """Add placeholder signature."""
        # Calculate content hash
        content = manifest.to_json()
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        manifest.signatures = {
            "primary": {
                "algorithm": "unsigned",
                "key_id": self.key_id,
                "content_hash": content_hash,
                "signed_at": datetime.utcnow().isoformat(),
            }
        }
        
        return manifest
    
    def verify(self, manifest: SignedManifest) -> bool:
        """Always returns True for unsigned manifests."""
        return True
