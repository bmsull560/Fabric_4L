#!/usr/bin/env python3
"""
Neo4j Query Profiler

Captures and analyzes query performance metrics from Neo4j.

Usage:
    python scripts/perf/profile-neo4j-queries.py \
        --neo4j-uri bolt://localhost:7687 \
        --user neo4j \
        --password secret \
        --analyze-slow-queries \
        --threshold 500

    python scripts/perf/profile-neo4j-queries.py \
        --continuous \
        --interval 60 \
        --prometheus-push http://prometheus-pushgateway:9091
"""

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Optional

from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Constants for query analysis thresholds
DEFAULT_SLOW_QUERY_THRESHOLD_MS = 500
DEFAULT_TOP_N_QUERIES = 20
DEFAULT_CONTINUOUS_INTERVAL_S = 60
HIGH_MEMORY_THRESHOLD_BYTES = 100 * 1024 * 1024  # 100MB
IO_BOUND_CPU_RATIO = 0.3
WAIT_TIME_CPU_RATIO = 0.5
LOW_CACHE_HIT_RATIO = 0.5
QUERY_TRUNCATE_LENGTH = 500
QUERY_PREVIEW_LENGTH = 200
QUERY_DISPLAY_LENGTH = 150


@dataclass
class QueryProfile:
    """Profiled query information."""
    query_id: str
    query_text: str
    elapsed_time_ms: float
    planning_time_ms: float
    cpu_time_ms: float
    wait_time_ms: float
    allocated_bytes: int
    page_cache_hits: int
    page_cache_misses: int
    hit_ratio: float
    timestamp: str
    metadata: dict = field(default_factory=dict)


@dataclass
class QueryPlan:
    """Query execution plan analysis."""
    query_id: str
    plan_description: str
    estimated_rows: int
    pipeline_info: list
    operators: list
    index_usage: list
    timestamp: str


class Neo4jQueryProfiler:
    """Profile Neo4j queries and generate performance reports."""
    
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        
    def connect(self):
        """Establish Neo4j connection."""
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
        )
        # Verify connectivity
        self.driver.verify_connectivity()
        
    def disconnect(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            
    def get_running_queries(self) -> list[dict]:
        """Get list of currently running queries."""
        with self.driver.session() as session:
            result = session.run("""
                SHOW TRANSACTIONS YIELD 
                    transactionId AS queryId,
                    currentQueryId,
                    elapsedTimeMillis,
                    cpuTimeMillis,
                    waitTimeMillis,
                    allocatedBytes,
                    pageHits,
                    pageFaults,
                    query
                RETURN {
                    queryId: queryId,
                    currentQueryId: currentQueryId,
                    elapsedTime: elapsedTimeMillis,
                    cpuTime: cpuTimeMillis,
                    waitTime: waitTimeMillis,
                    allocatedBytes: allocatedBytes,
                    pageHits: pageHits,
                    pageFaults: pageFaults,
                    query: query
                } AS info
            """)
            return [record["info"] for record in result]
    
    def get_slow_queries(self, threshold_ms: int = 500) -> list[QueryProfile]:
        """Get queries exceeding duration threshold."""
        with self.driver.session() as session:
            # Enable query logging if not already enabled
            session.run("CALL dbms.setConfigValue('dbms.logs.query.enabled', 'true')")
            
            result = session.run("""
                CALL db.stats.retrieve('QUERIES') YIELD section, data
                UNWIND data AS query
                WITH query
                WHERE query.elapsedTimeMillis > $threshold
                RETURN query
                ORDER BY query.elapsedTimeMillis DESC
                LIMIT 50
            """, threshold=threshold_ms)
            
            profiles = []
            for record in result:
                q = record["query"]
                hits = q.get("pageHits", 0)
                misses = q.get("pageFaults", 0)
                hit_ratio = hits / (hits + misses) if (hits + misses) > 0 else 0
                
                profile = QueryProfile(
                    query_id=q.get("queryId", "unknown"),
                    query_text=q.get("query", "")[:QUERY_TRUNCATE_LENGTH],
                    elapsed_time_ms=q.get("elapsedTimeMillis", 0),
                    planning_time_ms=q.get("planningTimeMillis", 0),
                    cpu_time_ms=q.get("cpuTimeMillis", 0),
                    wait_time_ms=q.get("waitTimeMillis", 0),
                    allocated_bytes=q.get("allocatedBytes", 0),
                    page_cache_hits=hits,
                    page_cache_misses=misses,
                    hit_ratio=hit_ratio,
                    timestamp=datetime.now(UTC).isoformat(),
                    metadata={
                        "runtime": q.get("runtime", "unknown"),
                        "pool": q.get("pool", "unknown"),
                    }
                )
                profiles.append(profile)
                
            return profiles
    
    def explain_query(self, query_text: str) -> Optional[QueryPlan]:
        """Get execution plan for a query.

        Args:
            query_text: The Cypher query to explain. Note: This is executed with
                EXPLAIN and should not contain user-modifiable content.

        Returns:
            QueryPlan with execution details, or None if explanation fails.
        """
        # SECURITY: EXPLAIN runs the query planner; only explain trusted queries
        # This is intended for profiling known slow queries, not arbitrary user input
        with self.driver.session() as session:
            try:
                # Use parameterized query to avoid injection risks
                result = session.run(
                    "EXPLAIN CYPHER runtime=slotted $query_text",
                    query_text=query_text,
                )
                plan = result.consume().profile
                operators, index_usage = self._extract_plan_operators(plan)
                
                return QueryPlan(
                    query_id="explained",
                    plan_description=str(plan)[:1000] if plan else "N/A",
                    estimated_rows=plan.rows if plan else 0,
                    pipeline_info=[],
                    operators=operators,
                    index_usage=list(set(index_usage)),
                    timestamp=datetime.now(UTC).isoformat(),
                )
            except Exception as e:
                logger.error("Failed to explain query: %s", e)
                return None

    def _extract_plan_operators(self, plan) -> tuple[list[dict], list[str]]:
        """Extract operators and index usage from query plan.

        Args:
            plan: The query plan profile from Neo4j.

        Returns:
            Tuple of (operators list, index usage list).
        """
        operators: list[dict] = []
        index_usage: list[str] = []

        def _extract_recursive(operator):
            operators.append({
                "name": operator.name,
                "rows": operator.rows,
                "db_hits": operator.db_hits,
                "time": operator.time,
            })
            if hasattr(operator, "index"):
                index_usage.append(operator.index)
            if hasattr(operator, "children"):
                for child in operator.children:
                    _extract_recursive(child)

        if plan:
            _extract_recursive(plan)

        return operators, index_usage

    def get_query_statistics(self) -> dict:
        """Get aggregate query statistics."""
        with self.driver.session() as session:
            # Query statistics from db.stats
            stats_result = session.run("""
                CALL db.stats.retrieve('QUERIES') YIELD section, data
                RETURN {
                    totalQueries: size(data),
                    avgElapsedTime: avg([q IN data | q.elapsedTimeMillis]),
                    maxElapsedTime: max([q IN data | q.elapsedTimeMillis]),
                    p95ElapsedTime: percentileDisc([q IN data | q.elapsedTimeMillis], 0.95),
                    totalPageHits: sum([q IN data | q.pageHits]),
                    totalPageFaults: sum([q IN data | q.pageFaults])
                } AS stats
            """)
            
            stats_record = stats_result.single()
            if stats_record:
                return stats_record["stats"]
            return {}
    
    def generate_optimization_recommendations(self, slow_queries: list[QueryProfile]) -> list[dict]:
        """Generate optimization recommendations for slow queries."""
        recommendations = []

        for query in slow_queries:
            recs = []

            # Check for high page cache misses
            if query.page_cache_misses > query.page_cache_hits:
                recs.append({
                    "type": "cache_optimization",
                    "description": "High page cache misses detected. Consider increasing Neo4j page cache size.",
                    "action": "Increase dbms.memory.pagecache.size",
                    "priority": "high" if query.hit_ratio < LOW_CACHE_HIT_RATIO else "medium",
                })

            # Check for high wait time (lock contention)
            if query.wait_time_ms > query.cpu_time_ms * WAIT_TIME_CPU_RATIO:
                recs.append({
                    "type": "lock_contention",
                    "description": "High wait time indicates lock contention. Review concurrent access patterns.",
                    "action": "Analyze query patterns for concurrent writes",
                    "priority": "high",
                })

            # Check for long elapsed time with low CPU time (I/O bound)
            if query.elapsed_time_ms > 1000 and query.cpu_time_ms < query.elapsed_time_ms * IO_BOUND_CPU_RATIO:
                recs.append({
                    "type": "io_optimization",
                    "description": "Query appears I/O bound. Consider adding indexes or optimizing data model.",
                    "action": "Review query plan and add appropriate indexes",
                    "priority": "medium",
                })

            # Check for high memory allocation
            if query.allocated_bytes > HIGH_MEMORY_THRESHOLD_BYTES:
                recs.append({
                    "type": "memory_optimization",
                    "description": f"High memory allocation ({query.allocated_bytes / 1024 / 1024:.1f} MB). "
                                   "Consider query refactoring or batching.",
                    "action": "Optimize query to reduce memory footprint",
                    "priority": "medium",
                })
            
            if recs:
                recommendations.append({
                    "query_id": query.query_id,
                    "query_preview": query.query_text[:QUERY_PREVIEW_LENGTH],
                    "elapsed_time_ms": query.elapsed_time_ms,
                    "recommendations": recs,
                })
        
        return recommendations
    
    def run_profiler(self, threshold_ms: int = DEFAULT_SLOW_QUERY_THRESHOLD_MS, top_n: int = DEFAULT_TOP_N_QUERIES) -> dict:
        """Run complete profiling analysis."""
        logger.info("Connecting to Neo4j at %s", self.uri)
        self.connect()

        try:
            logger.info("Collecting query statistics...")
            statistics = self.get_query_statistics()

            logger.info("Finding queries > %d ms...", threshold_ms)
            slow_queries = self.get_slow_queries(threshold_ms)

            logger.info("Generating recommendations...")
            recommendations = self.generate_optimization_recommendations(slow_queries[:top_n])

            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "neo4j_uri": self.uri,
                "threshold_ms": threshold_ms,
                "statistics": statistics,
                "slow_queries": [asdict(q) for q in slow_queries[:top_n]],
                "optimization_recommendations": recommendations,
                "summary": {
                    "total_slow_queries": len(slow_queries),
                    "queries_with_recommendations": len(recommendations),
                    "avg_slow_query_time": sum(q.elapsed_time_ms for q in slow_queries) / len(slow_queries) if slow_queries else 0,
                },
            }
        finally:
            self.disconnect()


def generate_report(analysis: dict, format: str = "text") -> str:
    """Generate human-readable report."""
    if format == "json":
        return json.dumps(analysis, indent=2)
    
    lines = [
        "=" * 80,
        "Neo4j Query Performance Profile",
        "=" * 80,
        f"Generated: {analysis['timestamp']}",
        f"Neo4j URI: {analysis['neo4j_uri']}",
        f"Slow Query Threshold: {analysis['threshold_ms']}ms",
        "",
        "Summary:",
        f"  Total Slow Queries: {analysis['summary']['total_slow_queries']}",
        f"  With Recommendations: {analysis['summary']['queries_with_recommendations']}",
        f"  Avg Slow Query Time: {analysis['summary']['avg_slow_query_time']:.2f}ms",
        "",
    ]
    
    if analysis['statistics']:
        stats = analysis['statistics']
        lines.extend([
            "Query Statistics:",
            f"  Total Queries: {stats.get('totalQueries', 'N/A')}",
            f"  Avg Elapsed Time: {stats.get('avgElapsedTime', 0):.2f}ms",
            f"  Max Elapsed Time: {stats.get('maxElapsedTime', 0):.2f}ms",
            f"  P95 Elapsed Time: {stats.get('p95ElapsedTime', 0):.2f}ms",
            f"  Total Page Hits: {stats.get('totalPageHits', 0)}",
            f"  Total Page Faults: {stats.get('totalPageFaults', 0)}",
            "",
        ])
    
    if analysis['slow_queries']:
        lines.extend([
            "Top Slow Queries:",
            "-" * 80,
        ])
        
        for i, query in enumerate(analysis['slow_queries'][:10], 1):
            hit_ratio_pct = query['hit_ratio'] * 100
            lines.extend([
                f"\n{i}. Query ID: {query['query_id']}",
                f"   Elapsed: {query['elapsed_time_ms']:.2f}ms "
                f"(Plan: {query['planning_time_ms']:.2f}ms, "
                f"CPU: {query['cpu_time_ms']:.2f}ms, "
                f"Wait: {query['wait_time_ms']:.2f}ms)",
                f"   Page Cache: {query['page_cache_hits']} hits, "
                f"{query['page_cache_misses']} misses "
                f"({hit_ratio_pct:.1f}% hit ratio)",
                f"   Memory: {query['allocated_bytes'] / 1024 / 1024:.2f} MB",
                f"   Query: {query['query_text'][:QUERY_DISPLAY_LENGTH]}...",
            ])
    
    if analysis['optimization_recommendations']:
        lines.extend([
            "",
            "Optimization Recommendations:",
            "-" * 80,
        ])
        
        for rec_group in analysis['optimization_recommendations']:
            lines.extend([
                f"\nQuery: {rec_group['query_preview'][:100]}...",
                f"Elapsed Time: {rec_group['elapsed_time_ms']:.2f}ms",
            ])
            
            for rec in rec_group['recommendations']:
                priority_icon = "🔴" if rec['priority'] == 'high' else "🟡"
                lines.extend([
                    f"  {priority_icon} [{rec['type'].upper()}] {rec['priority'].upper()}",
                    f"     {rec['description']}",
                    f"     Action: {rec['action']}",
                ])
    
    lines.extend([
        "",
        "=" * 80,
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Profile Neo4j query performance"
    )
    parser.add_argument(
        "--neo4j-uri",
        default="bolt://localhost:7687",
        help="Neo4j Bolt URI",
    )
    parser.add_argument(
        "--user",
        default="neo4j",
        help="Neo4j username",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Neo4j password",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_SLOW_QUERY_THRESHOLD_MS,
        help="Slow query threshold in milliseconds",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=DEFAULT_TOP_N_QUERIES,
        help="Number of slow queries to report",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously with interval",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_CONTINUOUS_INTERVAL_S,
        help="Sampling interval in seconds (for continuous mode)",
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    
    args = parser.parse_args()
    
    profiler = Neo4jQueryProfiler(
        uri=args.neo4j_uri,
        user=args.user,
        password=args.password,
    )
    
    if args.continuous:
        logger.info("Running continuous profiler (interval: %ds)", args.interval)
        logger.info("Press Ctrl+C to stop")

        try:
            while True:
                analysis = profiler.run_profiler(args.threshold, args.top_n)
                report = generate_report(analysis, args.format)
                print(report)  # Report goes to stdout

                if args.output:
                    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                    output_file = args.output.replace(".json", f"_{timestamp}.json")
                    with open(output_file, "w") as f:
                        json.dump(analysis, f, indent=2)
                    logger.info("Saved: %s", output_file)

                time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("Profiler stopped")
    else:
        analysis = profiler.run_profiler(args.threshold, args.top_n)
        report = generate_report(analysis, args.format)
        print(report)
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(analysis, f, indent=2)
            logger.info("Analysis saved to: %s", args.output)

        # Exit with error code if critical issues found
        critical_count = sum(
            1 for rec_group in analysis['optimization_recommendations']
            for rec in rec_group['recommendations']
            if rec['priority'] == 'high'
        )

        if critical_count > 0:
            logger.warning("%d critical optimization(s) found", critical_count)
            sys.exit(1)
        else:
            logger.info("Query performance acceptable")
            sys.exit(0)


if __name__ == "__main__":
    main()
