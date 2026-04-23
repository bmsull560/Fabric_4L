"""Evidence indexer for querying."""

import json
import logging
from pathlib import Path
from typing import Optional

from .models import EvidenceBundle, EvidenceCategory, EvidenceItem


class EvidenceIndexer:
    """Indexes evidence for querying and retrieval."""
    
    def __init__(self, index_path: Path):
        self.index_path = index_path
        self.logger = logging.getLogger("gated.indexer")
        self._index: dict = {}
        self._load_index()
    
    def add(self, bundle: EvidenceBundle) -> None:
        """Add evidence bundle to index."""
        if bundle.release_id not in self._index:
            self._index[bundle.release_id] = []
        
        self._index[bundle.release_id].append({
            "bundle_id": str(bundle.bundle_id),
            "gate_id": bundle.gate_id,
            "category": bundle.category.value,
            "timestamp": bundle.timestamp.isoformat(),
            "trace_id": bundle.trace_id,
            "items": [
                {
                    "path": str(item.path),
                    "checksum": item.checksum,
                    "size_bytes": item.size_bytes,
                    "category": item.category.value,
                }
                for item in bundle.items
            ],
        })
        
        self._save_index()
        self.logger.debug(f"Indexed bundle for {bundle.gate_id}")
    
    def query(
        self,
        release_id: Optional[str] = None,
        gate_id: Optional[str] = None,
        category: Optional[EvidenceCategory] = None,
    ) -> list[EvidenceItem]:
        """Query indexed evidence."""
        results = []
        
        releases = [release_id] if release_id else list(self._index.keys())
        
        for rel_id in releases:
            for bundle_data in self._index.get(rel_id, []):
                if gate_id and bundle_data["gate_id"] != gate_id:
                    continue
                
                if category and bundle_data["category"] != category.value:
                    continue
                
                for item_data in bundle_data["items"]:
                    results.append(EvidenceItem(
                        path=Path(item_data["path"]),
                        content_type="unknown",  # Not stored in index
                        checksum=item_data["checksum"],
                        size_bytes=item_data["size_bytes"],
                        category=EvidenceCategory(item_data["category"]),
                    ))
        
        return results
    
    def get_release_summary(self, release_id: str) -> dict:
        """Get summary of evidence for a release."""
        bundles = self._index.get(release_id, [])
        
        categories = {}
        gates = {}
        total_items = 0
        
        for bundle in bundles:
            cat = bundle["category"]
            categories[cat] = categories.get(cat, 0) + 1
            
            gate = bundle["gate_id"]
            gates[gate] = gates.get(gate, 0) + len(bundle["items"])
            
            total_items += len(bundle["items"])
        
        return {
            "release_id": release_id,
            "total_bundles": len(bundles),
            "total_items": total_items,
            "categories": categories,
            "gates": gates,
        }
    
    def _load_index(self) -> None:
        """Load index from disk."""
        if self.index_path.exists():
            try:
                with open(self.index_path) as f:
                    self._index = json.load(f)
            except json.JSONDecodeError:
                self.logger.warning("Failed to load index, starting fresh")
                self._index = {}
        else:
            self._index = {}
    
    def _save_index(self) -> None:
        """Save index to disk."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "w") as f:
            json.dump(self._index, f, indent=2)
