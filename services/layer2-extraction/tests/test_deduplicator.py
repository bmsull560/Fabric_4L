"""Tests for EntityDeduplicator._find_clusters() (layer2-extraction)."""

import numpy as np

from layer2_extraction.extraction.deduplicator import EntityDeduplicator


def _make_deduplicator(threshold: float = 0.85) -> EntityDeduplicator:
    obj = object.__new__(EntityDeduplicator)
    obj.threshold = threshold
    obj.similarity_threshold = threshold
    return obj


class TestFindClusters:
    def setup_method(self):
        self.dedup = _make_deduplicator(threshold=0.85)

    def test_all_dissimilar_returns_singletons(self):
        sim = np.array([[1.0, 0.1, 0.2], [0.1, 1.0, 0.3], [0.2, 0.3, 1.0]])
        clusters = self.dedup._find_clusters(sim)
        assert len(clusters) == 3
        assert all(len(c) == 1 for c in clusters)
        assert sorted(idx for c in clusters for idx in c) == [0, 1, 2]

    def test_all_similar_returns_one_cluster(self):
        sim = np.array([[1.0, 0.9, 0.95], [0.9, 1.0, 0.92], [0.95, 0.92, 1.0]])
        clusters = self.dedup._find_clusters(sim)
        assert len(clusters) == 1
        assert sorted(clusters[0]) == [0, 1, 2]

    def test_exactly_at_threshold_is_merged(self):
        sim = np.array([[1.0, 0.85], [0.85, 1.0]])
        clusters = self.dedup._find_clusters(sim)
        assert len(clusters) == 1
        assert sorted(clusters[0]) == [0, 1]

    def test_just_below_threshold_is_not_merged(self):
        sim = np.array([[1.0, 0.849], [0.849, 1.0]])
        clusters = self.dedup._find_clusters(sim)
        assert len(clusters) == 2
        assert all(len(c) == 1 for c in clusters)

    def test_transitive_cluster_bfs(self):
        sim = np.array([[1.0, 0.9, 0.5], [0.9, 1.0, 0.9], [0.5, 0.9, 1.0]])
        clusters = self.dedup._find_clusters(sim)
        assert len(clusters) == 1
        assert sorted(clusters[0]) == [0, 1, 2]

    def test_two_clusters_and_one_singleton(self):
        sim = np.array([
            [1.0, 0.9, 0.1, 0.2, 0.1],
            [0.9, 1.0, 0.1, 0.1, 0.2],
            [0.1, 0.1, 1.0, 0.3, 0.2],
            [0.2, 0.1, 0.3, 1.0, 0.88],
            [0.1, 0.2, 0.2, 0.88, 1.0],
        ])
        clusters = self.dedup._find_clusters(sim)
        assert len(clusters) == 3
        cluster_sets = {frozenset(c) for c in clusters}
        assert frozenset({0, 1}) in cluster_sets
        assert frozenset({3, 4}) in cluster_sets
        assert frozenset({2}) in cluster_sets

    def test_single_entity_returns_one_singleton(self):
        sim = np.array([[1.0]])
        clusters = self.dedup._find_clusters(sim)
        assert clusters == [[0]]

    def test_empty_matrix_returns_empty_list(self):
        sim = np.empty((0, 0))
        clusters = self.dedup._find_clusters(sim)
        assert clusters == []
