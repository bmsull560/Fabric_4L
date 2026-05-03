-- Layer 6 Benchmark Service — Initial Neo4j Schema
-- Run this script against your Neo4j instance before starting the service.
--
-- Usage (via cypher-shell or Neo4j Browser):
--   :use neo4j
--   CALL apoc.cypher.runFile('001_initial_schema.cypher') YIELD row RETURN row;
-- Or execute statements individually.

-- Unique constraint on BenchmarkDataset.dataset_id
CREATE CONSTRAINT benchmark_dataset_id IF NOT EXISTS
FOR (d:BenchmarkDataset)
REQUIRE d.dataset_id IS UNIQUE;

-- Unique constraint on BenchmarkMetric composite (dataset_id + name)
-- Neo4j 5 supports node property constraints only; relationship uniqueness
-- is enforced by application logic (MERGE on dataset_id then CREATE metric).
-- We add an index on metric name for fast lookups.
CREATE INDEX benchmark_metric_name IF NOT EXISTS
FOR (m:BenchmarkMetric)
ON (m.name);
