"""Tests for EntityDeduplicator._find_clusters() (layer2-extraction).

Imports the deduplicator module directly to avoid the OpenAI import-time
requirement and the value_fabric shared-package dependency.
Mirrors the direct-file-import pattern used in test_chunker.py.

External dependency stubs (openai, value_fabric) are registered in conftest.py
so they are in place before any test module is collected.
"""

import importlib.util
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Direct file import — mirrors the pattern used in test_chunker.py.
# ---------------------------------------------------------------------------
_dedup_path = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "layer2_extraction"
    / "extraction"
    / "deduplicator.py"
)
_spec = importlib.util.spec_from_file_location("deduplicator", _dedup_path)
_dedup_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dedup_mod)

EntityDeduplicator = _dedup_mod.EntityDeduplicator


# ---------------------------------------------------------------------------
# Helper: build an EntityDeduplicator without touching the OpenAI client.
# ---------------------------------------------------------------------------
def _make_deduplicator(threshold: float = 0.85) -> EntityDeduplicator:
    obj = object.__new__(EntityDeduplicator)
    obj.threshold = threshold
    return obj


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFindClusters:
    """Unit tests for EntityDeduplicator._find_clusters()."""

    def setup_method(self):
        self.dedup = _make_deduplicator(threshold=0.85)

    # -- all entities are distinct -------------------------------------------

    def test_all_dissimilar_returns_singletons(self):
        sim = np.array([
            [1.0, 0.1, 0.2],
            [0.1, 1.0, 0.3],
            [0.2, 0.3, 1.0],
        ])
        clusters = self.dedup._find_clusters(sim)

        assert len(clusters) == 3
        assert all(len(c) == 1 for c in clusters)
        assert sorted(idx for c in clusters for idx in c) == [0, 1, 2]

    # -- all entities are duplicates -----------------------------------------

    def test_all_similar_returns_one_cluster(self):
        sim = np.array([
            [1.0,  0.9,  0.95],
            [0.9,  1.0,  0.92],
            [0.95, 0.92, 1.0],
        ])
        clusters = self.dedup._find_clusters(sim)

        assert len(clusters) == 1
        assert sorted(clusters[0]) == [0, 1, 2]

    # -- threshold boundary --------------------------------------------------

    def test_exactly_at_threshold_is_merged(self):
        # >= threshold means exactly 0.85 must be merged
        sim = np.array([
            [1.0,  0.85],
            [0.85, 1.0],
        ])
        clusters = self.dedup._find_clusters(sim)

        assert len(clusters) == 1
        assert sorted(clusters[0]) == [0, 1]

    def test_just_below_threshold_is_not_merged(self):
        sim = np.array([
            [1.0,   0.849],
            [0.849, 1.0],
        ])
        clusters = self.dedup._find_clusters(sim)

        assert len(clusters) == 2
        assert all(len(c) == 1 for c in clusters)

    # -- transitive BFS clustering -------------------------------------------

    def test_transitive_cluster_bfs(self):
        # A≈B and B≈C but A≉C — BFS must still group all three together
        sim = np.array([
            [1.0, 0.9, 0.5],
            [0.9, 1.0, 0.9],
            [0.5, 0.9, 1.0],
        ])
        clusters = self.dedup._find_clusters(sim)

        assert len(clusters) == 1
        assert sorted(clusters[0]) == [0, 1, 2]

    # -- mixed: two clusters + one singleton ---------------------------------

    def test_two_clusters_and_one_singleton(self):
        # 0,1 → cluster A;  2 → singleton;  3,4 → cluster B
        sim = np.array([
            [1.0,  0.9,  0.1,  0.2,  0.1],
            [0.9,  1.0,  0.1,  0.1,  0.2],
            [0.1,  0.1,  1.0,  0.3,  0.2],
            [0.2,  0.1,  0.3,  1.0,  0.88],
            [0.1,  0.2,  0.2,  0.88, 1.0],
        ])
        clusters = self.dedup._find_clusters(sim)

        assert len(clusters) == 3
        cluster_sets = {frozenset(c) for c in clusters}
        assert frozenset({0, 1}) in cluster_sets
        assert frozenset({3, 4}) in cluster_sets
        assert frozenset({2}) in cluster_sets
        assert sorted(idx for c in clusters for idx in c) == [0, 1, 2, 3, 4]

    # -- single entity -------------------------------------------------------

    def test_single_entity_returns_one_singleton(self):
        sim = np.array([[1.0]])
        clusters = self.dedup._find_clusters(sim)

        assert clusters == [[0]]

    # -- empty matrix --------------------------------------------------------

    def test_empty_matrix_returns_empty_list(self):
        sim = np.empty((0, 0))
        clusters = self.dedup._find_clusters(sim)

        assert clusters == []
