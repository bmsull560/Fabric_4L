# Value Fabric System Architecture
## Production Ingestion: HTTP Fast Path + Stagehand Browser Fallback + Neo4j

**Version:** 1.0.0  
**Status:** PRODUCTION-READY  
**Date:** April 2026

---

## 1. Executive Summary

Extracting structured value ontologies from vendor websites at scale requires handling three conflicting requirements simultaneously:

1. **Speed**: Static pages should be processed in milliseconds, not seconds.
2. **Accuracy**: JavaScript-heavy Single Page Applications (SPAs) need real browser rendering + structured extraction.
3. **Cost**: Browser automation is 50-100x more expensive than HTTP fetching.

### The Solution

Value Fabric utilizes a **dual-path hybrid architecture** that routes pages intelligently:

| Path | Technology | When to Use | Relative Cost | Speed |
|------|-----------|-------------|---------------|-------|
| **Fast Path** | HTTPX + HTML parser | Static pages, sitemaps, known structures | 1x | ~200ms |
| **Browser Path** | Stagehand v3 + Browserbase | Dynamic content, navigation, structured extraction | 50-100x | ~3-8s |
| **Smart Router** | Heuristic + ML classifier | Decides which path per-page | — | <10ms decision |

---

## 2. High-Level Architecture

### 2.1 System Diagram

```text
                              EXTERNAL SOURCES
                         +-------------------------+
                         |   Vendor Sitemap/RSS    |
                         |   https://vendor.com/   |
                         +------------+------------+
                                      |
                                      v
+============================================================================+
|                           ORCHESTRATION LAYER                              |
|  +------------------+  +------------------+  +---------------------------+ |
|  |  Airflow DAG     |  |  URL Registry    |  |  Crawl State Machine      | |
|  |  (scheduler)     |  |  (PostgreSQL)    |  |  ( discovered / queued /  | |
|  |                  |  |                  |  |    scraped / extracted /  | |
|  |  vendor_crawl_dag|  |  url_queue table |  |    ingested / failed )    | |
|  +--------+---------+  +--------+---------+  +---------------------------+ |
|           |                     |                                          |
+===========|=====================|==========================================+
            |                     |
            v                     v
+============================================================================+
|                           INGESTION LAYER                                  |
|                                                                            |
|  +-------------------------+        +----------------------------------+   |
|  |   SMART ROUTER          |        |   BROWSER POOL MANAGER           |   |
|  |   (routing decision)    |        |   (Browserbase session mgmt)     |   |
|  |                         |        |                                  |   |
|  |  Input: URL + metadata  |        |  - Session lifecycle (create/    |   |
|  |  Output: FAST or BROWSER|        |    recycle/destroy)              |   |
|  |                         |        |  - Concurrency control           |   |
|  |  Rules:                 |        |  - Cost tracking per session     |   |
|  |  1. In sitemap_static?  |        |  - Retry with fresh session      |   |
|  |     -> FAST             |        |    on failure                    |   |
|  |  2. Previous crawl used |        |                                  |   |
|  |     browser? -> same    |        |  Max concurrent: 25 (Dev plan)   |   |
|  |  3. Contains #, ?, modal|        |  Session TTL: 6 hours            |   |
|  |     -> BROWSER          |        |  Warm pool: 3 sessions           |   |
|  |  4. robots.txt says JS? |        +----------------------------------+   |
|  |     -> BROWSER          |                      |                       |
|  |  5. Else -> FAST first, |                      |                       |
|  |     fallback BROWSER    |                      v                       |
|  |     on empty result     |        +----------------------------------+   |
|  +-----------+-------------+        |   BROWSERBASE CLOUD               |   |
|              |                       |                                  |   |
|     +--------+--------+              |  +-----------------------------+ |   |
|     |                 |              |  | Headless Chromium (CDP)     | |   |
|     v                 v              |  | - Stagehand v3 (CDP-native) | |   |
|  +------+      +-------------+      |  | - Auto iframe/shadow DOM    | |   |
|  | FAST |      |   BROWSER   |<-----+  | - Session replay            | |   |
|  | PATH |      |    PATH     |      |  | - Stealth mode              | |   |
|  +------+      +-------------+      |  +-----------------------------+ |   |
|     |                 |              +----------------------------------+   |
|     v                 v                                                    |
|  +-------------------------------+                                         |
|  |   RAW CONTENT STORE (S3/MinIO)|                                         |
|  |   - HTML snapshots              |                                         |
|  |   - Screenshots (browser path)  |                                         |
|  |   - Text extractions            |                                         |
|  |   - Provenance metadata         |                                         |
|  +-------------------------------+                                         |
+============================================================================+
            |
            v
+============================================================================+
|                           EXTRACTION LAYER                                 |
|                                                                            |
|  +------------------+  +------------------+  +-------------------------+   |
|  | Page Classifier  |  | Entity Extractor |  | Relationship Extractor  |   |
|  | (LLM + rules)    |  | (Pydantic schemas|  | (LLM + heuristics)      |   |
|  |                  |  |  per page type)  |  |                         |   |
|  | 11 page types:   |  |                  |  | 50 relationship types    |   |
|  | HOMEPAGE, PRODUCT|  | 57 entity types  |  | from ontology schema     |   |
|  | ROLE_SOLUTION... |  |                  |  |                         |   |
|  +--------+---------+  +--------+---------+  +------------+------------+   |
|           |                     |                         |                |
|           +----------+----------+------------+            |                |
|                      v                      v             |                |
|  +-------------------------------+  +---------------------+-----+          |
|  |   Value Extraction Record     |  |   Confidence Scorer         |          |
|  |   (VER - JSON per page)       |  |   (algorithmic scoring)     |          |
|  |                               |  |                             |          |
|  | {                             |  | Score = Base x Type x       |          |
|  |   source_url,                 |  |         (1+Corr) x Temporal |          |
|  |   page_type,                  |  |                             |          |
|  |   extracted: { entities },    |  | Governance gates:           |          |
|  |   relationships: [],          |  | - No ValueDriver without    |          |
|  |   confidence_scores,          |  |   Metric or ProofPoint      |          |
|  |   trace_spans                 |  | - No Product claim without  |          |
|  | }                             |  |   Capability evidence       |          |
|  +---------------+---------------+  +--------------+--------------+          |
|                  |                                 |                       |
+==================|=================================|=======================+
                   |                                 |
                   v                                 v
+============================================================================+
|                           NORMALIZATION LAYER                              |
|                                                                            |
|  +------------------------+  +------------------------+                    |
|  | Value Normalizer       |  | Metric Canonicalizer   |                    |
|  |                        |  |                        |                    |
|  | Raw phrase ->          |  | "Up to 50%" ->         |                    |
|  | Canonical driver       |  | 0.50 (conservative)    |                    |
|  |                        |  |                        |                    |
|  | 82 normalization rules |  | 35 canonical metric    |                    |
|  | from ontology schema   |  | types with units       |                    |
|  +-----------+------------+  +-----------+------------+                    |
|              |                           |                                 |
|              +-------------+-------------+                                 |
|              |                                                             |
|              v                                                             |
|  +--------------------------------------------------+                      |
|  | Canonical EntityRef Generation                   |                      |
|  |                                                  |                      |
|  | - Canonical value drivers                        |                      |
|  | - Normalized metrics with units                  |                      |
|  | - Confidence scores                              |                      |
|  +------------------------+-------------------------+                      |
|                           |                                                |
+===========================|================================================+
                            v
+============================================================================+
|                           GRAPH LAYER                                      |
|                                                                            |
|  +------------------------+  +------------------------+                    |
|  | Neo4j Batch Builder    |  | Graph Validator        |                    |
|  |                        |  |                        |                    |
|  | Cypher MERGE patterns  |  | 5 governance gates     |                    |
|  | - Nodes: ~30 labels    |  | with Cypher checks     |                    |
|  | - Edges: ~45 types     |  |                        |                    |
|  | - Batch size: 500      |  | Post-ingestion         |                    |
|  | - Unwind for speed     |  | validation queries     |                    |
|  +-----------+------------+  +-----------+------------+                    |
|              |                           |                                 |
|              v                           v                                 |
|  +--------------------------------------------------+                      |
|  | Neo4j 5.x (AuraDB or self-hosted)                |                      |
|  |                                                  |                      |
|  |  - Property Graph Model                          |                      |
|  |  - 15 constraints (unique/existence)             |                      |
|  |  - 15 performance indexes                        |                      |
|  |  - Full-text search on names/descriptions        |                      |
|  |  - Query API for downstream consumers            |                      |
|  +--------------------------------------------------+                      |
+============================================================================+
```

---

## 3. Component Deep Dives

### 3.1 Smart Router

The router makes the FAST vs BROWSER decision in <10ms using a cascading rule engine. It detects SPA shells (e.g., `<div id="root"></div>`) and automatically routes them to the Browser Path.

### 3.2 Fast Path (HTTPX)

Utilizes `httpx` for asynchronous fetching and `trafilatura` for clean text extraction. If it detects a JS-rendered SPA shell during parsing, it signals the router to fall back to the Browser Path.

### 3.3 Browser Path (Stagehand v3)

Utilizes Stagehand v3 for browser automation, managed via Browserbase for session pooling. It uses Pydantic schemas for structured extraction directly from the rendered DOM, minimizing token usage by scoping `extract()` calls with `observe()`.

---

## 4. Integration with Artifact Contracts

The output of this ingestion pipeline directly populates the Neo4j graph using the canonical `EntityRef` schema defined in the Value Fabric Artifact Contracts. This ensures that the `ContextExtractionAgent` and `ValueModelAgent` consume strictly typed, provenance-aware entities.
