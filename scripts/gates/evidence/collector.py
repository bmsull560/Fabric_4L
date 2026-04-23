"""Evidence collection for audit compliance."""

import hashlib
import logging
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from sdk.models import GateArtifact, GateExecution

from .models import AuditBundle, EvidenceBundle, EvidenceCategory, EvidenceItem


class EvidenceCollector:
    """Collects evidence for audit compliance."""
    
    # Map gate IDs to SOC2 categories
    GATE_CATEGORIES = {
        "security": EvidenceCategory.SECURITY_OPERATIONS,
        "contract": EvidenceCategory.SECURITY_OPERATIONS,
        "arch": EvidenceCategory.CHANGE_MANAGEMENT,
        "smoke": EvidenceCategory.AVAILABILITY,
        "chaos": EvidenceCategory.AVAILABILITY,
        "agent": EvidenceCategory.CHANGE_MANAGEMENT,
        "state": EvidenceCategory.AVAILABILITY,
        "obs": EvidenceCategory.AVAILABILITY,
    }
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.logger = logging.getLogger("gated.evidence")
        self.bundles: list[EvidenceBundle] = []
    
    def collect_gate_evidence(
        self,
        execution: GateExecution,
        release_id: Optional[str] = None,
    ) -> EvidenceBundle:
        """
        Collect evidence from a gate execution.
        
        Args:
            execution: Gate execution
            release_id: Optional release identifier
            
        Returns:
            Evidence bundle
        """
        category = self.GATE_CATEGORIES.get(execution.gate_id, EvidenceCategory.POLICIES)
        
        bundle = EvidenceBundle(
            category=category,
            gate_id=execution.gate_id,
            release_id=release_id,
            trace_id=execution.trace_id,
        )
        
        # Convert artifacts to evidence items
        for artifact in execution.artifacts:
            item = self._artifact_to_item(artifact, category)
            bundle.items.append(item)
        
        self.bundles.append(bundle)
        self.logger.info(f"Collected evidence for {execution.gate_id}: {len(bundle.items)} items")
        
        return bundle
    
    def _artifact_to_item(
        self,
        artifact: GateArtifact,
        category: EvidenceCategory,
    ) -> EvidenceItem:
        """Convert gate artifact to evidence item."""
        return EvidenceItem(
            path=artifact.path,
            content_type=artifact.content_type,
            checksum=artifact.checksum,
            size_bytes=artifact.size_bytes,
            category=category,
            metadata={
                "gate_id": artifact.path.parent.name if artifact.path.parent.name != "artifacts" else "unknown",
            },
        )
    
    def generate_audit_bundle(
        self,
        release_id: str,
        include_system_files: bool = True,
    ) -> Path:
        """
        Generate SOC2/ISO27001 compliant audit bundle.
        
        Args:
            release_id: Release identifier
            include_system_files: Include policy/config files
            
        Returns:
            Path to generated tar.gz bundle
        """
        bundle_path = self.output_dir / f"evidence-{release_id}.tar.gz"
        
        with tarfile.open(bundle_path, "w:gz") as tar:
            # Add gate evidence
            for evidence_bundle in self.bundles:
                category_dir = evidence_bundle.category.value
                
                for item in evidence_bundle.items:
                    arcname = f"{category_dir}/{evidence_bundle.gate_id}/{item.path.name}"
                    tar.add(item.path, arcname=arcname)
            
            # Add system files if requested
            if include_system_files:
                self._add_system_files(tar)
            
            # Generate and add manifest
            manifest = self._generate_manifest(release_id)
            manifest_path = self.output_dir / "manifest.json"
            manifest_path.write_text(str(manifest))
            tar.add(manifest_path, arcname="manifest.json")
        
        # Calculate bundle checksum
        checksum = self._calculate_checksum(bundle_path)
        
        self.logger.info(f"Generated audit bundle: {bundle_path} (sha256:{checksum[:16]}...)")
        
        return bundle_path
    
    def _add_system_files(self, tar: tarfile.TarFile) -> None:
        """Add system policy/config files to bundle."""
        system_files = [
            ("policies", ".fabric/prod-gates.policy.yaml"),
            ("policies", "SECURITY.md"),
            ("policies", "COMPLIANCE.md"),
            ("policies", "CONTRACT.md"),
            ("config", ".github/workflows/prod-readiness.yml"),
            ("config", "Makefile"),
        ]
        
        for category, file_path in system_files:
            path = Path(file_path)
            if path.exists():
                tar.add(path, arcname=f"{category}/{path.name}")
    
    def _generate_manifest(self, release_id: str) -> dict:
        """Generate bundle manifest."""
        items_by_category = {}
        
        for bundle in self.bundles:
            cat = bundle.category.value
            if cat not in items_by_category:
                items_by_category[cat] = []
            
            for item in bundle.items:
                items_by_category[cat].append({
                    "path": str(item.path),
                    "checksum": item.checksum,
                    "size_bytes": item.size_bytes,
                    "gate_id": bundle.gate_id,
                })
        
        return {
            "manifest_version": "1.0",
            "release_id": release_id,
            "timestamp": datetime.utcnow().isoformat(),
            "categories": items_by_category,
            "total_items": sum(len(items) for items in items_by_category.values()),
        }
    
    def _calculate_checksum(self, path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
