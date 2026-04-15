#!/usr/bin/env python3
"""
PostgreSQL Connection Pool Utilization Analyzer

Analyzes connection pool metrics and provides tuning recommendations.

Usage:
    python scripts/perf/analyze-connection-pools.py \
        --prometheus-url http://prometheus:9090 \
        --duration 30m \
        --output pool-analysis.json

    python scripts/perf/analyze-connection-pools.py \
        --kube-context value-fabric \
        --namespace value-fabric \
        --analyze-all-layers
"""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional

import requests


@dataclass
class PoolMetrics:
    """Connection pool metrics snapshot."""
    layer: str
    pool_size: int
    checked_in: float
    checked_out: float
    overflow: float
    wait_time_avg: float
    wait_time_p95: float
    utilization_percent: float
    timestamp: str


@dataclass
class TuningRecommendation:
    """Recommendation for pool tuning."""
    layer: str
    current_pool_size: int
    recommended_pool_size: int
    current_overflow: int
    recommended_overflow: int
    reason: str
    confidence: str  # high, medium, low
    action: str


class ConnectionPoolAnalyzer:
    """Analyze connection pool metrics and generate recommendations."""
    
    def __init__(self, prometheus_url: str, timeout: int = 30):
        self.prometheus_url = prometheus_url
        self.timeout = timeout
        self.session = requests.Session()
        
    def query_prometheus(self, query: str, time_range: str = "30m") -> dict:
        """Query Prometheus for metrics."""
        url = f"{self.prometheus_url}/api/v1/query"
        params = {
            "query": query,
            "time": datetime.utcnow().isoformat(),
        }
        
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def query_range(self, query: str, start: datetime, end: datetime, step: str = "60s") -> dict:
        """Query Prometheus range."""
        url = f"{self.prometheus_url}/api/v1/query_range"
        params = {
            "query": query,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "step": step,
        }
        
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def get_pool_metrics(self, layer: str, duration: str = "30m") -> Optional[PoolMetrics]:
        """Get connection pool metrics for a layer."""
        try:
            # Query pool size
            pool_size_result = self.query_prometheus(
                f'sqlalchemy_pool_size{{layer="{layer}"}}'
            )
            pool_size = float(pool_size_result["data"]["result"][0]["value"][1]) if pool_size_result["data"]["result"] else 20
            
            # Query checked in connections
            checked_in_result = self.query_prometheus(
                f'sqlalchemy_pool_checkedin{{layer="{layer}"}}'
            )
            checked_in = float(checked_in_result["data"]["result"][0]["value"][1]) if checked_in_result["data"]["result"] else 0
            
            # Query overflow
            overflow_result = self.query_prometheus(
                f'sqlalchemy_pool_overflow{{layer="{layer}"}}'
            )
            overflow = float(overflow_result["data"]["result"][0]["value"][1]) if overflow_result["data"]["result"] else 0
            
            # Query wait time
            wait_time_result = self.query_prometheus(
                f'histogram_quantile(0.95, rate(sqlalchemy_pool_wait_time_seconds_bucket{{layer="{layer}"}}[{duration}]))'
            )
            wait_time_p95 = float(wait_time_result["data"]["result"][0]["value"][1]) if wait_time_result["data"]["result"] else 0
            
            # Calculate utilization
            utilization = ((pool_size - checked_in + overflow) / pool_size) * 100 if pool_size > 0 else 0
            
            return PoolMetrics(
                layer=layer,
                pool_size=int(pool_size),
                checked_in=checked_in,
                checked_out=pool_size - checked_in,
                overflow=overflow,
                wait_time_avg=wait_time_p95 * 0.5,  # Estimate
                wait_time_p95=wait_time_p95,
                utilization_percent=utilization,
                timestamp=datetime.utcnow().isoformat(),
            )
        except Exception as e:
            print(f"Error querying metrics for {layer}: {e}", file=sys.stderr)
            return None
    
    def analyze_pool(self, metrics: PoolMetrics) -> TuningRecommendation:
        """Analyze pool metrics and generate recommendation."""
        current_size = metrics.pool_size
        current_overflow = int(metrics.overflow)
        
        # Determine recommendation based on utilization patterns
        if metrics.utilization_percent > 90 and metrics.overflow > 0:
            # Pool exhausted with overflow usage
            recommended_size = int(current_size * 1.5)
            recommended_overflow = int(recommended_size * 0.5)
            reason = f"Pool exhausted ({metrics.utilization_percent:.1f}% util, {metrics.overflow} overflow connections)"
            confidence = "high"
            action = "Increase pool_size and max_overflow immediately"
            
        elif metrics.utilization_percent > 80:
            # High utilization but no overflow
            recommended_size = int(current_size * 1.25)
            recommended_overflow = int(current_size * 0.5)
            reason = f"High utilization ({metrics.utilization_percent:.1f}%) approaching limit"
            confidence = "medium"
            action = "Monitor closely; increase pool_size if trend continues"
            
        elif metrics.utilization_percent < 30 and metrics.wait_time_p95 < 0.1:
            # Low utilization, fast response - pool oversized
            recommended_size = max(int(current_size * 0.7), 5)
            recommended_overflow = max(int(recommended_size * 0.5), 3)
            reason = f"Low utilization ({metrics.utilization_percent:.1f}%) with fast response times"
            confidence = "medium"
            action = "Consider reducing pool_size to free resources"
            
        elif metrics.wait_time_p95 > 1.0:
            # High wait times indicate contention
            recommended_size = int(current_size * 1.3)
            recommended_overflow = int(current_size * 0.5)
            reason = f"High wait times (p95: {metrics.wait_time_p95:.2f}s) indicate connection contention"
            confidence = "high"
            action = "Increase pool_size and investigate query duration"
            
        else:
            # Pool appropriately sized
            recommended_size = current_size
            recommended_overflow = max(int(current_size * 0.5), 5)
            reason = f"Pool appropriately sized ({metrics.utilization_percent:.1f}% util, {metrics.wait_time_p95:.3f}s wait)"
            confidence = "high"
            action = "No changes required"
        
        return TuningRecommendation(
            layer=metrics.layer,
            current_pool_size=current_size,
            recommended_pool_size=recommended_size,
            current_overflow=current_overflow,
            recommended_overflow=recommended_overflow,
            reason=reason,
            confidence=confidence,
            action=action,
        )
    
    def analyze_all_layers(self, layers: list[str], duration: str = "30m") -> dict:
        """Analyze connection pools for all layers."""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "prometheus_url": self.prometheus_url,
            "analysis_duration": duration,
            "layers": {},
            "recommendations": [],
            "summary": {
                "total_pools_analyzed": 0,
                "pools_needing_attention": 0,
                "high_confidence_recommendations": 0,
            },
        }
        
        for layer in layers:
            metrics = self.get_pool_metrics(layer, duration)
            if metrics:
                results["layers"][layer] = asdict(metrics)
                recommendation = self.analyze_pool(metrics)
                results["recommendations"].append(asdict(recommendation))
                
                results["summary"]["total_pools_analyzed"] += 1
                if recommendation.current_pool_size != recommendation.recommended_pool_size:
                    results["summary"]["pools_needing_attention"] += 1
                if recommendation.confidence == "high":
                    results["summary"]["high_confidence_recommendations"] += 1
        
        return results


def generate_report(analysis: dict, format: str = "text") -> str:
    """Generate human-readable report."""
    if format == "json":
        return json.dumps(analysis, indent=2)
    
    lines = [
        "=" * 70,
        "PostgreSQL Connection Pool Analysis Report",
        "=" * 70,
        f"Generated: {analysis['timestamp']}",
        f"Duration: {analysis['analysis_duration']}",
        f"Source: {analysis['prometheus_url']}",
        "",
        f"Summary:",
        f"  Pools Analyzed: {analysis['summary']['total_pools_analyzed']}",
        f"  Need Attention: {analysis['summary']['pools_needing_attention']}",
        f"  High Confidence: {analysis['summary']['high_confidence_recommendations']}",
        "",
        "Current Pool Metrics:",
        "-" * 70,
    ]
    
    for layer, metrics in analysis["layers"].items():
        lines.extend([
            f"\n{layer.upper()}",
            f"  Pool Size: {metrics['pool_size']}",
            f"  Checked In: {metrics['checked_in']:.1f}",
            f"  Overflow: {metrics['overflow']:.1f}",
            f"  Utilization: {metrics['utilization_percent']:.1f}%",
            f"  Wait Time p95: {metrics['wait_time_p95']:.3f}s",
        ])
    
    lines.extend([
        "",
        "Recommendations:",
        "-" * 70,
    ])
    
    for rec in analysis["recommendations"]:
        action_marker = "🔴" if rec["current_pool_size"] != rec["recommended_pool_size"] else "🟢"
        lines.extend([
            f"\n{action_marker} {rec['layer'].upper()}",
            f"  Current: {rec['current_pool_size']} (+{rec['current_overflow']} overflow)",
            f"  Recommended: {rec['recommended_pool_size']} (+{rec['recommended_overflow']} overflow)",
            f"  Confidence: {rec['confidence'].upper()}",
            f"  Reason: {rec['reason']}",
            f"  Action: {rec['action']}",
        ])
    
    lines.extend([
        "",
        "=" * 70,
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze PostgreSQL connection pool utilization"
    )
    parser.add_argument(
        "--prometheus-url",
        default="http://localhost:9090",
        help="Prometheus server URL",
    )
    parser.add_argument(
        "--duration",
        default="30m",
        help="Analysis time range (e.g., 30m, 1h, 24h)",
    )
    parser.add_argument(
        "--layers",
        nargs="+",
        default=["layer1", "layer2", "layer3", "layer4", "layer5", "layer6"],
        help="Layers to analyze",
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
    parser.add_argument(
        "--apply-recommendations",
        action="store_true",
        help="Generate Kubernetes manifest patches (dry-run)",
    )
    
    args = parser.parse_args()
    
    # Run analysis
    analyzer = ConnectionPoolAnalyzer(args.prometheus_url)
    analysis = analyzer.analyze_all_layers(args.layers, args.duration)
    
    # Generate report
    report = generate_report(analysis, args.format)
    print(report)
    
    # Save to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(analysis, f, indent=2)
        print(f"\nAnalysis saved to: {args.output}")
    
    # Generate manifest patches if requested
    if args.apply_recommendations:
        print("\n" + "=" * 70)
        print("Kubernetes Manifest Patches (apply with kubectl patch)")
        print("=" * 70)
        
        for rec in analysis["recommendations"]:
            if rec["current_pool_size"] != rec["recommended_pool_size"]:
                patch = {
                    "spec": {
                        "template": {
                            "metadata": {
                                "annotations": {
                                    "postgres.pool.size": str(rec["recommended_pool_size"]),
                                    "postgres.pool.max-overflow": str(rec["recommended_overflow"]),
                                }
                            }
                        }
                    }
                }
                print(f"\n{rec['layer']}:")
                print(json.dumps(patch, indent=2))
    
    # Exit with error code if pools need attention
    if analysis["summary"]["pools_needing_attention"] > 0:
        print(f"\n⚠️  {analysis['summary']['pools_needing_attention']} pool(s) need attention")
        sys.exit(1)
    else:
        print("\n✅ All pools appropriately sized")
        sys.exit(0)


if __name__ == "__main__":
    main()
